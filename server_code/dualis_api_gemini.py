import anvil.server
import itertools
from concurrent import futures
import requests
from bs4 import BeautifulSoup
from functools import partial

# BASE_URL global definieren
BASE_URL = "https://dualis.dhbw.de"

# --- Helferfunktionen auf Modulebene ---
# (Akzeptieren jetzt das 'session'-Objekt statt cookies/headers)

def parse_student_results(url, session):
  response = session.get(url=url)
  student_result_soup = BeautifulSoup(response.content, "html.parser")
  table = student_result_soup.find("table", {"class": "students_results"})
  if not table:
    return []
  return [a['href'] for a in table.find_all("a", href=True)]


def parse_semester(url, session):
  semester_response = session.get(url)
  semester_soup = BeautifulSoup(semester_response.content, 'html.parser')
  table = semester_soup.find("table", {"class": "list"})
  if not table:
    return []
  return [script.text.strip()[301:414] for script in table.find_all("script")]


def parse_unit(url, session):
  response = session.get(url=BASE_URL + url)
  detail_soup = BeautifulSoup(response.content, "html.parser")

  h1_tag = detail_soup.find("h1")
  if not h1_tag:
    return {'name': 'Unbekanntes Modul', 'exams': []}

  h1 = h1_tag.text.strip()
  table = detail_soup.find("table", {"class": "tb"})

  unit = {'name': h1.replace("\n", " ").replace("\r", ""), 'exams': []}

  if not table:
    return unit 

  td = [td.text.strip() for td in table.find_all("td")]

  try:
    if len(td) <= 24:
      exam = {'name': td[13], 'date': td[14], 'grade': td[15], 'externally accepted': False}
      unit['exams'].append(exam)
    elif len(td) <= 29:
      exam = {'name': td[19], 'date': td[14], 'grade': td[21], 'externally accepted': False}
      unit['exams'].append(exam)
    elif len(td) == 30:
      for idx in range(13, len(td) - 5, 6):
        exam = {'name': td[idx], 'date': td[idx + 1], 'grade': td[idx + 2], 'externally accepted': False}
        unit['exams'].append(exam)
    elif len(td) <= 31:
      for idx in range(11, len(td) - 7, 7):
        exam = {'name': td[idx], 'date': td[idx + 3], 'grade': td[idx + 4], 'externally accepted': False}
        unit['exams'].append(exam)
    else:
      for idx in range(19, len(td) - 5, 6):
        exam = {'name': td[idx], 'date': td[14], 'grade': td[idx + 2], 'externally accepted': False}
        unit['exams'].append(exam)
  except IndexError:
    pass 

  return unit


def logout(url, session):
  return session.get(url=url).ok

# --- Haupt-Serverfunktion ---

@anvil.server.callable
def scrape_data_gemini(user, password):
  units = []

  url = BASE_URL + "/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=EXTERNALPAGES&ARGUMENTS=-N000000000000001,-N000324,-Awelcome"

  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
    'Host': 'dualis.dhbw.de',
    'Origin': BASE_URL,
    'Referer': url
  }

  # NEU: Session-Objekt erstellen
  session = requests.Session()

  # NEU: Header für die gesamte Session setzen
  session.headers.update(headers)

  try:
    # 1. Session erstellen (Session holt sich Cookies)
    # Wir brauchen die 'cookie_request' Variable nicht mehr, da die Session die Cookies intern speichert
    session.get(url) 

    data = {"usrname": user, "pass": password, 
            "APPNAME": "CampusNet",
            "PRGNAME": "LOGINCHECK",
            "ARGUMENTS": "clino,usrname,pass,menuno,menu_type, browser,platform",
            "clino": "000000000000001",
            "menuno": "000324",
            "menu_type": "classic",
            "browser": "",
            "platform": ""
           }

    # 2. Login-Versuch (Session sendet Cookies automatisch mit)
    login_response = session.post(url, data=data, verify=True) 

    # 3. Login-Erfolg prüfen
    if not login_response.ok:
      if login_response.status_code == 403:
        return None, "Login-Server-Fehler: 403 (Session-Versuch fehlgeschlagen). IP-Sperre wahrscheinlich."
      return None, f"Login-Server-Fehler: {login_response.status_code}"

    if 'REFRESH' not in login_response.headers:
      soup = BeautifulSoup(login_response.content, 'html.parser')
      error_msg = soup.find('div', {'class': 'error-messages'})
      if error_msg:
        return None, error_msg.text.strip()
      return None, "Login fehlgeschlagen. Prüfen Sie Anmeldedaten."

    arguments = login_response.headers['REFRESH']

    # HINWEIS: Wir müssen 'session_cookies' nicht mehr extrahieren.

    # 4. Zu den Notenseiten navigieren
    url_content = BASE_URL + "/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=STARTPAGE_DISPATCH&ARGUMENTS=" + arguments[79:]
    url_content = url_content.replace("STARTPAGE_DISPATCH", "COURSERESULTS")

    semester_ids_response = session.get(url_content) 

    if not semester_ids_response.ok:
      return None, f"Fehler beim Laden der Semesterseite: {semester_ids_response.status_code}"
            
        # 5. Semester-IDs und URLs finden
    soup = BeautifulSoup(semester_ids_response.content, 'html.parser')
    options = soup.find_all('option')
    semester_ids = [option['value'] for option in options]
    semester_urls = [url_content[:-15] + semester_id for semester_id in semester_ids]
    
    # 6. Modul-URLs parallel abrufen
    # NEU: Wir übergeben das 'session'-Objekt an partial
    parse_semester_partial = partial(parse_semester, session=session)
    
    with futures.ThreadPoolExecutor(8) as semester_pool:
        tmp = semester_pool.map(parse_semester_partial, semester_urls) 
    unit_urls = list(itertools.chain.from_iterable(tmp))
    
    if not unit_urls:
          return None, "Login erfolgreich, aber keine Modul-URLs gefunden."

    # 7. Noten (Units) parallel abrufen
    # NEU: Wir übergeben das 'session'-Objekt an partial
    parse_unit_partial = partial(parse_unit, session=session)
    
    with futures.ThreadPoolExecutor(8) as detail_pool:
        semester_results = list(detail_pool.map(parse_unit_partial, unit_urls)) 
    units.extend(semester_results) 
    
    # 8. Logout
    logout_link = soup.find('a', {'id': 'logoutButton'})
    if logout_link:
        logout_url = BASE_URL + logout_link['href']
        logout(logout_url, session=session) 
    
    # 9. Daten "flachklopfen"
    flat_grades_list = []
    for unit in units:
        module_name = unit.get('name', 'Unbekanntes Modul')
        if not unit.get('exams') or len(unit.get('exams')) == 0:
            pass 
        else:
            for exam in unit['exams']:
                exam_name = exam.get('name', 'Unbekannte Prüfung')
                
                if exam_name == module_name:
                      full_name = module_name
                else:
                      full_name = f"{module_name} - {exam_name}"
                      
                flat_grades_list.append({
                    'name': full_name,
                    'grade': exam.get('grade', '-'),
                    'cp': '-' 
                })

    if not flat_grades_list:
        return None, "Login erfolgreich, aber keine Noten gefunden."

    # 10. Erfolg!
    return flat_grades_list, None
  except Exception as e:
    return None, f"Ein unerwarteter Server-Fehler ist aufgetreten: {str(e)}"