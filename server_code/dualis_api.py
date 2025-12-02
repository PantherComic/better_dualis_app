import anvil.server
import requests
from bs4 import BeautifulSoup
import time
import re

BASE_URL = "https://dualis.dhbw.de"

@anvil.server.callable
def get_grades(user, password):

  print("--- Neue 'get_grades' Anfrage gestartet ---")

  all_grades = []
  student_name = "Unbekannt"

  if not user or not password:
    print("Fehler: Benutzer oder Passwort nicht angegeben.")
    raise anvil.server.PermissionDenied("Benutzername und Passwort dürfen nicht leer sein.")

    # 1. Einzige Session für alle Anfragen erstellen
  with requests.Session() as s:

    # 2. User-Agent
    s.headers.update({
      'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    })

    # 3. 'Referer'-Header für Login
    login_page_referer = BASE_URL + "/"
    s.headers.update({'Referer': login_page_referer})
    print(f"Setze 'Referer'-Header auf: {login_page_referer}")

    # 4. POST-Endpunkt und 'cnsc=0' Cookie
    login_post_url = BASE_URL + "/scripts/mgrqispi.dll/"
    print("Setze 'cnsc=0' Cookie vor dem Login.")
    s.cookies.set('cnsc', '0')

    # 5. Login-Daten und POST
    login_data = {"usrname": user, "pass": password,
                  "APPNAME": "CampusNet", "PRGNAME": "LOGINCHECK",
                  "ARGUMENTS": "clino,usrname,pass,menuno,menu_type, browser,platform",
                  "clino": "000000000000001", "menuno": "000324",
                  "menu_type": "classic", "browser": "", "platform": ""
                 }
    try:
      print(f"Sende Login-POST für Benutzer: {user} an {login_post_url}...")
      login_response = s.post(login_post_url, data=login_data, verify=True, timeout=10)
      print(f"Login-Antwort erhalten, Status: {login_response.status_code}")
    except requests.RequestException as e:
      print(f"FEHLER bei Login-Anfrage: {e}")
      raise Exception(f"Login-Anfrage fehlgeschlagen: {e}")

      # 6. REFRESH-Header-Prüfung und Parsing
    if 'REFRESH' not in login_response.headers:
      print("FEHLER: 'REFRESH'-Header nicht in der Login-Antwort. Login fehlgeschlagen.")
      raise anvil.server.PermissionDenied("Login fehlgeschlagen. Bitte Benutzername und Passwort prüfen.")

    print("Login erfolgreich, 'REFRESH'-Header gefunden.")
    refresh_header = login_response.headers['REFRESH']
    match = re.search(r'URL=(.*)', refresh_header)

    if not match:
      print(f"FEHLER: Konnte 'URL=' nicht im REFRESH-Header finden: {refresh_header}")
      raise Exception("Login-Antwort-Parsing fehlgeschlagen.")

    redirect_path = match.group(1).replace("STARTPAGE_DISPATCH", "COURSERESULTS")
    url_content = BASE_URL + redirect_path
    print(f"Weiterleitungs-URL (Semester-Hauptseite) geparst: {url_content}")

    # 7. Semester-Hauptseite abrufen (mit GET)
    try:
      print("Rufe Semester-Hauptseite ab...")
      s.headers.update({'Referer': login_page_referer})
      semester_ids_response = s.get(url_content, timeout=10)
      print(f"Semester-Hauptseite erhalten, Status: {semester_ids_response.status_code}")
    except requests.RequestException as e:
      print(f"FEHLER beim Abruf der Semester-Hauptseite: {e}")
      raise Exception(f"Semester-Abfrage fehlgeschlagen: {e}")

    if not semester_ids_response.ok:
      raise Exception(f"Semester-Abfrage fehlgeschlagen mit Statuscode: {semester_ids_response.status_code}")

      # 8. ALLES PARSEN: Semester-Daten, Formular-Daten UND Name
    soup = BeautifulSoup(semester_ids_response.content, 'html.parser')

    try:
      name_span = soup.find('span', {'class': 'loginDataName'})
      if name_span:
        student_name = name_span.text.strip()
        # BEREINIGUNG: Entfernt "Name: "
        student_name = student_name.replace('Name:', '').replace('"', '').strip()
        print(f"Studentenname gefunden und bereinigt: {student_name}")
      else:
        print("DEBUG: Span 'class=loginDataName' konnte nicht im HTML gefunden werden.")
    except Exception as e:
      print(f"FEHLER beim Parsen des Studentennamens: {e}")

      # Semester-Daten (ID und Name) aus dem Dropdown
    options = soup.find_all('option')
    semester_data_list = [(option['value'], option.text.strip()) for option in options] 

    # Versteckte Formular-Daten für den POST-Befehl auslesen
    try:
      form_data = {}
      form = soup.find('form', {'id': 'semesterchange'})
      if not form:
        print("FEHLER: Konnte 'semesterchange'-Formular nicht auf der Seite finden. HTML ist unerwartet.")
        raise Exception("Konnte Semester-Formular nicht finden.")
      form_action_url = BASE_URL + form['action']
      hidden_inputs = form.find_all('input', {'type': 'hidden'})
      for input_tag in hidden_inputs:
        name = input_tag.get('name')
        value = input_tag.get('value', '')
        if name: 
          form_data[name] = value
      print(f"Formular-Daten geparst: {form_data}")
    except Exception as e:
      print(f"FEHLER beim Parsen der Formular-Daten: {e}")
      raise Exception("Fehler beim Parsen der Semester-Formulardaten.")

    print(f"{len(semester_data_list)} Semester im Dropdown gefunden.")

    # 9. Einzelne Semesterseiten abrufen
    for i, (sem_id, sem_name) in enumerate(semester_data_list):
      try:
        print(f"Aktualisiere 'Referer'-Header auf: {url_content}")
        s.headers.update({'Referer': url_content})
        post_payload = form_data.copy()
        post_payload['semester'] = sem_id
        print(f"Verarbeite Semester {i+1}/{len(semester_data_list)} (ID: {sem_id}, Name: {sem_name}). Sende POST...")
        semester_response = s.post(form_action_url, data=post_payload, timeout=10)

        if semester_response.ok:
          semester_grades = parse_semester_overview(semester_response.content, sem_name)
          all_grades.extend(semester_grades)
        else:
          print(f"WARNUNG: POST-Anfrage für Semester-ID {sem_id} schlug fehl, Status: {semester_response.status_code}")
      except requests.RequestException as e:
        print(f"FEHLER beim Abrufen von Semester-ID {sem_id}: {e}")
        continue 

    print(f"{len(all_grades)} Lerneinheiten insgesamt gefunden.")

    # 10. Logout
    s.headers.update({'Referer': url_content})
    logout_button = soup.find('a', {'id': 'logoutButton'})
    if logout_button and 'href' in logout_button.attrs:
      logout_url = BASE_URL + logout_button['href']
      print("Führe Logout durch...")
      s.get(logout_url, timeout=10) 

    print(f"--- 'get_grades' Anfrage erfolgreich beendet. {len(all_grades)} Lerneinheiten gefunden. ---")

    # Gibt ein Wörterbuch statt nur einer Liste zurück
  return {
    'student_name': student_name,
    'grades': all_grades
  }


# ----- HILFSFUNKTIONEN -----

def parse_semester_overview(html_content, semester_name):

  print(f"DEBUG (parse_semester_overview): Beginne HTML-Parsing für Semester: {semester_name}.")
  semester_soup = BeautifulSoup(html_content, 'html.parser')
  table = semester_soup.find("table", {"class": "nb list"})

  if not table:
    print("DEBUG (parse_semester_overview): Konnte Tabelle 'nb list' NICHT finden.")
    body_tag = semester_soup.find('body')
    if body_tag:
      print(f"DEBUG: Body-Inhalt (falls Fehlerseite): {body_tag.text[:500]}...")
    return []

  print("DEBUG (parse_semester_overview): Tabelle 'nb list' GEFUNDEN.")
  grades_list = []

  try:
    rows = table.find('tbody').find_all('tr')
  except AttributeError:
    rows = table.find_all('tr')

  if not rows:
    print("DEBUG (parse_semester_overview): Tabelle 'nb list' gefunden, aber keine Zeilen (tr) darin.")
    return []

  for row in rows[:-1]: 
    cols = row.find_all('td')
    if len(cols) >= 5:
      try:
        unit_name = cols[1].text.strip()
        grade = cols[2].text.strip()
        credits = cols[3].text.strip()
        status = cols[4].text.strip()

        if unit_name == "Semester-GPA" or unit_name == "":
          continue

        unit = {
          'semester_name': semester_name,
          'name': unit_name,
          'exams': [{
            'name': 'Endnote', 
            'date': '',       
            'grade': grade,
            'status': status,
            'cp': credits,
            'externally accepted': False
          }]
        }
        grades_list.append(unit)
      except Exception as e:
        print(f"FEHLER (parse_semester_overview): Konnte Zeile nicht parsen. Fehler: {e}. Zeileninhalt: {[c.text for c in cols]}")
        continue
  print(f"DEBUG (parse_semester_overview): {len(grades_list)} Noten in Tabelle 'nb list' gefunden.")
  return grades_list


# --- Anvil Server Uplink ---
if __name__ == "__main__":
  anvil.server.connect("DEIN_UPLINK_SCHLÜSSEL_HIER") 
  print("Verbunden mit Anvil. Warte auf Funktionsaufrufe...")
  anvil.server.wait_forever()