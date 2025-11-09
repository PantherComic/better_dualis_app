import anvil.server
import requests
from bs4 import BeautifulSoup
import time
import re # Zum Parsen des REFRESH-Headers

BASE_URL = "https://dualis.dhbw.de"

@anvil.server.callable
def get_semesters():
  return {}

@anvil.server.callable
def get_units():
  return {}

@anvil.server.callable
def get_grades(user, password):
  """
    Anvil-Serverfunktion zur Abfrage von Noten.
    
    Korrektur 6: Aktualisiert den 'Referer'-Header vor dem Abrufen
    der einzelnen Semester, um sicherzustellen, dass wir die
    korrekte HTML-Seite mit der Notentabelle erhalten.
    """

  print(f"--- Neue 'get_grades' Anfrage gestartet ---")

  all_grades = []

  if not user or not password:
    print("Fehler: Benutzer oder Passwort nicht angegeben.")
    raise anvil.server.PermissionDenied("Benutzername und Passwort dürfen nicht leer sein.")

    # 1. Einzige Session für alle Anfragen erstellen
  with requests.Session() as s:

    # 2. User-Agent SETZEN
    s.headers.update({
      'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    })

    # 3. 'Referer'-Header für Login
    login_page_referer = BASE_URL + "/"
    s.headers.update({'Referer': login_page_referer})
    print(f"Setze 'Referer'-Header auf: {login_page_referer}")

    # Der POST-Endpunkt
    post_url = BASE_URL + "/scripts/mgrqispi.dll/"

    # 4. 'cnsc=0' Cookie manuell setzen
    print("Setze 'cnsc=0' Cookie vor dem Login.")
    s.cookies.set('cnsc', '0')

    # Daten-Payload
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

    # 5. Login-POST
    try:
      print(f"Sende Login-POST für Benutzer: {user} an {post_url}...")
      login_response = s.post(post_url, data=data, verify=True, timeout=10)
      print(f"Login-Antwort erhalten, Status: {login_response.status_code}")
    except requests.RequestException as e:
      print(f"FEHLER bei Login-Anfrage: {e}")
      raise Exception(f"Login-Anfrage fehlgeschlagen: {e}")

    if not login_response.ok:
      print(f"FEHLER: Login-Antwort nicht OK, Status: {login_response.status_code}")
      raise Exception(f"Login-Anage fehlgeschlagen mit Statuscode: {login_response.status_code}")

    if 'REFRESH' not in login_response.headers:
      print("FEHLER: 'REFRESH'-Header nicht in der Login-Antwort. Login fehlgeschlagen.")
      raise anvil.server.PermissionDenied("Login fehlgeschlagen. Bitte Benutzername und Passwort prüfen.")

    print("Login erfolgreich, 'REFRESH'-Header gefunden.")

    # 6. REFRESH-Header parsen
    refresh_header = login_response.headers['REFRESH']
    match = re.search(r'URL=(.*)', refresh_header)
    if not match:
      print(f"FEHLER: Konnte URL nicht im REFRESH-Header finden: {refresh_header}")
      raise Exception("Login-Weiterleitung fehlgeschlagen.")

    redirect_path = match.group(1)
    redirect_path = redirect_path.replace("STARTPAGE_DISPATCH", "COURSERESULTS")
    url_content = BASE_URL + redirect_path # Dies ist die URL der Semester-Hauptseite

    print(f"Weiterleitungs-URL (Semester-Hauptseite) geparst: {url_content}")

    # 7. Semester-Hauptseite abrufen
    try:
      print("Rufe Semester-Hauptseite ab...")
      # Der 'Referer' ist immer noch die Login-Seite, was für diesen ersten GET ok ist
      semester_ids_response = s.get(url_content, timeout=10)
      print(f"Semester-Hauptseite erhalten, Status: {semester_ids_response.status_code}")
    except requests.RequestException as e:
      print(f"FEHLER beim Abruf der Semester-Hauptseite: {e}")
      raise Exception(f"Semester-Abfrage fehlgeschlagen: {e}")

    if not semester_ids_response.ok:
      print(f"FEHLER: Semester-Abfrage fehlgeschlagen, Status: {semester_ids_response.status_code}")
      raise Exception(f"Semester-Abfrage fehlgeschlagen mit Statuscode: {semester_ids_response.status_code}")

      # 8. Semester-IDs aus dem Dropdown auslesen
    soup = BeautifulSoup(semester_ids_response.content, 'html.parser')
    options = soup.find_all('option')
    semester_ids = [option['value'] for option in options]
    base_argument_url = url_content.split('ARGUMENTS=')[0] + "ARGUMENTS="
    semester_urls = [base_argument_url + sem_id for sem_id in semester_ids]
    print(f"{len(semester_urls)} Semester-URLs gefunden.")

    # 9. Einzelne Semesterseiten abrufen (SEQUENZIELL)
    for i, sem_url in enumerate(semester_urls):
      try:
        # --- HIER IST DIE KORREKTUR (KORREKTUR 6) ---
        # Wir aktualisieren den 'Referer'-Header, um so zu tun, als ob
        # wir von der Semester-Hauptseite kommen.
        print(f"Aktualisiere 'Referer'-Header auf: {url_content}")
        s.headers.update({'Referer': url_content})
        # --- ENDE KORREKTUR ---

        print(f"Verarbeite Semester {i+1}/{len(semester_urls)}...")
        semester_response = s.get(sem_url, timeout=10)

        if semester_response.ok:
          semester_grades = parse_semester_overview(semester_response.content)
          all_grades.extend(semester_grades)
        else:
          print(f"WARNUNG: Anfrage für Semester-URL {sem_url} schlug fehl, Status: {semester_response.status_code}")
          # Drucke den HTML-Inhalt der Fehlerseite
          print(f"FEHLER-HTML: {semester_response.text[:500]}...") 

      except requests.RequestException as e:
        print(f"FEHLER beim Abrufen von Semester-URL {sem_url}: {e}")
        continue 

    print(f"{len(all_grades)} Lerneinheiten insgesamt gefunden.")

    # 10. Logout
    # Setze den Referer zurück (gute Praxis)
    s.headers.update({'Referer': url_content})
    logout_button = soup.find('a', {'id': 'logoutButton'})
    if logout_button and 'href' in logout_button.attrs:
      logout_url = BASE_URL + logout_button['href']
      print("Führe Logout durch...")
      s.get(logout_url, timeout=10) 

    print(f"--- 'get_grades' Anfrage erfolgreich beendet. {len(all_grades)} Lerneinheiten gefunden. ---")

  return all_grades


# ----- HILFSFUNKTIONEN -----

def parse_semester_overview(html_content):
  """
    Parst die Noten-ÜBERSICHTS-Tabelle (die 'nb list' Tabelle).
    """

  # Debug-Ausgabe, um zu sehen, was wir WIRKLICH bekommen
  print(f"DEBUG (parse_semester_overview): Beginne HTML-Parsing. Erhaltene HTML (erste 1000 Zeichen):\n{html_content[:1000]}\n")

  semester_soup = BeautifulSoup(html_content, 'html.parser')

  # Suchen nach der Tabelle, die im Screenshot und Referenzcode zu sehen ist
  table = semester_soup.find("table", {"class": "nb list"})

  if not table:
    print("DEBUG (parse_semester_overview): Konnte Tabelle 'nb list' NICHT finden.")
    # Drucke den Body, um zu sehen, ob es eine Fehlerseite ist
    body_tag = semester_soup.find('body')
    if body_tag:
      print(f"DEBUG: Body-Inhalt: {body_tag.text[:500]}...")
    return []

  print("DEBUG (parse_semester_overview): Tabelle 'nb list' GEFUNDEN.")
  grades_list = []

  try:
    rows = table.find('tbody').find_all('tr')
  except AttributeError:
    rows = table.find_all('tr') # Fallback

  if not rows:
    print("DEBUG (parse_semester_overview): Tabelle 'nb list' gefunden, aber keine Zeilen (tr) darin.")
    return []

    # Die letzte Zeile ist oft der GPA (Notendurchschnitt), wir überspringen sie
  for row in rows[:-1]: 
    cols = row.find_all('td')

    if len(cols) >= 5:
      try:
        unit_name = cols[1].text.strip()
        grade = cols[2].text.strip()
        status = cols[4].text.strip()

        unit = {
          'name': unit_name,
          'exams': [{
            'name': 'Endnote', 
            'date': '',       
            'grade': grade,
            'status': status,
            'externally accepted': False
          }]
        }
        grades_list.append(unit)

      except Exception as e:
        print(f"FEHLER (parse_semester_overview): Konnte Zeile nicht parsen. Fehler: {e}")
        continue

  print(f"DEBUG (parse_semester_overview): {len(grades_list)} Noten in Tabelle 'nb list' gefunden.")
  return grades_list


# --- HINZUGEFÜGT: Anvil Server Uplink ---
if __name__ == "__main__":
  anvil.server.connect("DEIN_UPLINK_SCHLÜSSEL_HIER") 

  print("Verbunden mit Anvil. Warte auf Funktionsaufrufe...")
  anvil.server.wait_forever()