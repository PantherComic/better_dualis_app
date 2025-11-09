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
    
    Korrektur 7: Sendet einen POST (anstatt GET), um die einzelnen
    Semesterseiten abzurufen, basierend auf dem 'semesterchange'-Formular.
    Korrektur 8: Liest 'Credits' (CPs) aus der Tabelle aus.
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

    # Der POST-Endpunkt für den Login
    login_post_url = BASE_URL + "/scripts/mgrqispi.dll/"

    # 4. 'cnsc=0' Cookie manuell setzen
    print("Setze 'cnsc=0' Cookie vor dem Login.")
    s.cookies.set('cnsc', '0')

    # Daten-Payload für Login
    login_data = {"usrname": user, "pass": password,
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
      print(f"Sende Login-POST für Benutzer: {user} an {login_post_url}...")
      login_response = s.post(login_post_url, data=login_data, verify=True, timeout=10)
      print(f"Login-Antwort erhalten, Status: {login_response.status_code}")
    except requests.RequestException as e:
      print(f"FEHLER bei Login-Anfrage: {e}")
      raise Exception(f"Login-Anfrage fehlgeschlagen: {e}")

      # Login-Prüfungen
    if not login_response.ok:
      print(f"FEHLER: Login-Antwort nicht OK, Status: {login_response.status_code}")
      raise Exception(f"Login-Anfrage fehlgeschlagen mit Statuscode: {login_response.status_code}")

    if 'REFRESH' not in login_response.headers:
      print("FEHLER: 'REFRESH'-Header nicht in der Login-Antwort. Login fehlgeschlagen.")
      raise anvil.server.PermissionDenied("Login fehlgeschlagen. Bitte Benutzername und Passwort prüfen.")

    print("Login erfolgreich, 'REFRESH'-Header gefunden.")

    # 6. REFRESH-Header parsen
    refresh_header = login_response.headers['REFRESH']
    match = re.search(r'URL=(.*)', refresh_header)
    if not match:
      print(f"FEHLER: Konnte URL nicht aus REFRESH-Header parsen: {refresh_header}")
      raise Exception("Login-Redirect fehlgeschlagen.")

    redirect_path = match.group(1).replace("STARTPAGE_DISPATCH", "COURSERESULTS")
    url_content = BASE_URL + redirect_path # Dies ist die URL der Semester-Hauptseite

    print(f"Weiterleitungs-URL (Semester-Hauptseite) geparst: {url_content}")

    # 7. Semester-Hauptseite abrufen (mit GET)
    try:
      print("Rufe Semester-Hauptseite ab...")
      s.headers.update({'Referer': login_page_referer}) # Referer ist noch die Login-Seite
      semester_ids_response = s.get(url_content, timeout=10)
      print(f"Semester-Hauptseite erhalten, Status: {semester_ids_response.status_code}")
    except requests.RequestException as e:
      print(f"FEHLER beim Abruf der Semester-Hauptseite: {e}")
      raise Exception(f"Semester-Abfrage fehlgeschlagen: {e}")

    if not semester_ids_response.ok:
      raise Exception(f"Semester-Abfrage fehlgeschlagen mit Statuscode: {semester_ids_response.status_code}")

      # 8. Semester-IDs UND Formular-Daten auslesen
    soup = BeautifulSoup(semester_ids_response.content, 'html.parser')

    # Semester-IDs aus dem Dropdown
    options = soup.find_all('option')
    semester_ids = [option['value'] for option in options]

    # Versteckte Formular-Daten für den POST-Befehl auslesen
    try:
      form_data = {}
      form = soup.find('form', {'id': 'semesterchange'})
      if not form:
        print("FEHLER: Konnte 'semesterchange'-Formular nicht auf der Seite finden. HTML ist unerwartet.")
        raise Exception("Konnte Semester-Formular nicht finden.")

      form_action_url = BASE_URL + form['action'] # z.B. /scripts/mgrqispi.dll

      hidden_inputs = form.find_all('input', {'type': 'hidden'})
      for input_tag in hidden_inputs:
        name = input_tag.get('name')
        value = input_tag.get('value', '') # Nimm leeren String, falls value fehlt
        if name:
          form_data[name] = value

      print(f"Formular-Daten geparst: {form_data}")

    except Exception as e:
      print(f"FEHLER beim Parsen der Formular-Daten: {e}")
      print(f"HTML der Seite (erste 1000 Zeichen): {semester_ids_response.content[:1000]}")
      raise Exception("Fehler beim Parsen der Semester-Formulardaten.")

    print(f"{len(semester_ids)} Semester-IDs im Dropdown gefunden.")

    # 9. Einzelne Semesterseiten abrufen (jetzt mit POST)
    for i, sem_id in enumerate(semester_ids):
      try:
        # 1. Den 'Referer'-Header auf die Seite setzen, von der wir "posten"
        print(f"Aktualisiere 'Referer'-Header auf: {url_content}")
        s.headers.update({'Referer': url_content})

        # 2. Die POST-Daten vorbereiten
        post_payload = form_data.copy()
        post_payload['semester'] = sem_id # Das ist das Dropdown-Feld

        print(f"Verarbeite Semester {i+1}/{len(semester_ids)} (ID: {sem_id}). Sende POST...")

        # 3. Den POST-Befehl senden
        semester_response = s.post(form_action_url, data=post_payload, timeout=10)

        if semester_response.ok:
          semester_grades = parse_semester_overview(semester_response.content)
          all_grades.extend(semester_grades)
        else:
          print(f"WARNUNG: POST-Anfrage für Semester-ID {sem_id} schlug fehl, Status: {semester_response.status_code}")
          print(f"FEHLER-HTML: {semester_response.text[:500]}...") 

      except requests.RequestException as e:
        print(f"FEHLER beim Abrufen von Semester-ID {sem_id}: {e}")
        continue 

    print(f"{len(all_grades)} Lerneinheiten insgesamt gefunden.")

    # 10. Logout
    s.headers.update({'Referer': url_content}) # Referer ist die letzte Seite, die wir besucht haben
    logout_button = soup.find('a', {'id': 'logoutButton'})
    if logout_button and 'href' in logout_button.attrs:
      logout_url = BASE_URL + logout_button['href']
      print("Führe Logout durch...")
      s.get(logout_url, timeout=10) 

    print(f"--- 'get_grades' Anfrage erfolgreich beendet. {len(all_grades)} Lerneinheiten gefunden. ---")

  return all_grades


# ----- HILFSFUNKTIONEN (Aktualisiert) -----

def parse_semester_overview(html_content):
  """
    Parst die Noten-ÜBERSICHTS-Tabelle (die 'nb list' Tabelle).
    Liest jetzt auch Credits (CPs) aus.
    """

  print(f"DEBUG (parse_semester_overview): Beginne HTML-Parsing...")

  semester_soup = BeautifulSoup(html_content, 'html.parser')

  # Suchen nach der Tabelle, die im Screenshot und Referenzcode zu sehen ist
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
    # Fallback, falls <tbody> nicht existiert
    rows = table.find_all('tr')

  if not rows:
    print("DEBUG (parse_semester_overview): Tabelle 'nb list' gefunden, aber keine Zeilen (tr) darin.")
    return []

    # Die letzte Zeile ist oft der GPA (Notendurchschnitt), wir überspringen sie
  for row in rows[:-1]: 
    cols = row.find_all('td')

    # Erhöhte Stabilität: Sicherstellen, dass wir genug Spalten haben
    if len(cols) >= 5: # Brauchen mind. 5 Spalten (Name, Note, CP, Status)
      try:
        unit_name = cols[1].text.strip()
        grade = cols[2].text.strip()
        cp = cols[3].text.strip() # <-- KORREKTUR: Credits (CPs)
        status = cols[4].text.strip()

        # Leere Zeilen überspringen (z.B. nur '&nbsp;')
        if not unit_name and not grade and not status:
          continue

        unit = {
          'name': unit_name,
          'exams': [{
            'name': 'Endnote', 
            'date': '',       
            'grade': grade,
            'status': status,
            'cp': cp, # <-- KORREKTUR: Hinzugefügt
            'externally accepted': False
          }]
        }
        grades_list.append(unit)

      except Exception as e:
        print(f"FEHLER (parse_semester_overview): Konnte Zeile nicht parsen. Fehler: {e}. Zeileninhalt: {row.text}")
        continue
    else:
      print(f"DEBUG (parse_semester_overview): Zeile übersprungen, da sie nicht genug Spalten (<5) hatte.")

  print(f"DEBUG (parse_semester_overview): {len(grades_list)} Noten in Tabelle 'nb list' gefunden.")
  return grades_list


# --- HINZUGEFÜGT: Anvil Server Uplink ---
if __name__ == "__main__":
  # Ersetzen Sie dies mit Ihrem Anvil Uplink Key
  anvil.server.connect("DEIN_UPLINK_SCHLÜSSEL_HIER") 

  print("Verbunden mit Anvil. Warte auf Funktionsaufrufe...")
  anvil.server.wait_forever()