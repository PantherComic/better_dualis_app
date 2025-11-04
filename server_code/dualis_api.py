import anvil.server
import itertools
from concurrent import futures
import requests
from bs4 import BeautifulSoup

# --- Alle Flask-Imports wurden entfernt ---
# from flask import Flask, jsonify, request
# from werkzeug.exceptions import abort

BASE_URL = "https://dualis.dhbw.de"
# Die globale Variable 'units' wurde entfernt.


@anvil.server.callable
def get_semesters():
  # TODO: refactor code so that semesters can be accessed through endpoint
  # Gibt ein einfaches Dictionary zurück
  return {}


@anvil.server.callable
def get_units():
  # TODO: refactor code so that units and all relating exams can be accessed through endpoint
  # Gibt ein einfaches Dictionary zurück
  return {}


@anvil.server.callable
def get_grades(user, password):
  """
  Anvil-Serverfunktion zur Abfrage von Noten von dualis.dhbw.de.
  Erwartet user und password als direkte Funktionsargumente.
  :param user: Der Benutzername
  :param password: Das Passwort
  :return: Eine Liste von Dictionaries mit den Noten aller Semester.
  """

  # 'units' wird hier initialisiert, damit jede Anfrage eine eigene, leere Liste hat.
  units = [] 

  # --- Flask-Code (request.json) wurde entfernt ---
  # 'user' und 'password' kommen direkt als Funktionsargumente.

  # Einfache Validierung
  if not user or not password:
    raise anvil.server.PermissionDenied("Benutzername und Passwort dürfen nicht leer sein.")

  # create a session
  url = BASE_URL + "/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=EXTERNALPAGES&ARGUMENTS=-N000000000000001,-N000324,-Awelcome"
  cookie_request = requests.get(url)

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

  login_response = requests.post(url, data=data, headers=None, verify=True, cookies=cookie_request.cookies)

  # --- Bessere Fehlerbehandlung (ersetzt 'abort') ---
  if not login_response.ok:
    raise Exception(f"Login-Anfrage fehlgeschlagen mit Statuscode: {login_response.status_code}")

  # Prüfen, ob Login erfolgreich war (REFRESH Header ist vorhanden)
  if 'REFRESH' not in login_response.headers:
    raise anvil.server.PermissionDenied("Login fehlgeschlagen. Bitte Benutzername und Passwort prüfen.")

  arguments = login_response.headers['REFRESH']

  # redirecting to course results...
  url_content = BASE_URL + "/scripts/mgrqcgi?APPNAME=CampusNet&PRGNAME=STARTPAGE_DISPATCH&ARGUMENTS=" + arguments[79:]
  url_content = url_content.replace("STARTPAGE_DISPATCH", "COURSERESULTS")
  semester_ids_response = requests.get(url_content, cookies=login_response.cookies)

  if not semester_ids_response.ok:
    # Ersetzt 'abort'
    raise Exception(f"Semester-Abfrage fehlgeschlagen mit Statuscode: {semester_ids_response.status_code}")

  # get ids of all semester, replaces -N ...
  soup = BeautifulSoup(semester_ids_response.content, 'html.parser')
  options = soup.find_all('option')
  semester_ids = [option['value'] for option in options]
  semester_urls = [url_content[:-15] + semester_id for semester_id in semester_ids]

  # search for all unit_urls in parallel
  with futures.ThreadPoolExecutor(8) as semester_pool:
    tmp = semester_pool.map(parse_semester, semester_urls, [login_response.cookies] * len(semester_urls))
  unit_urls = list(itertools.chain.from_iterable(tmp))

  # query all unit_urls to obtain grades in parallel
  with futures.ThreadPoolExecutor(8) as detail_pool:
    semester = detail_pool.map(parse_unit, unit_urls, [login_response.cookies] * len(unit_urls))
  units.extend(semester)

  # find logout url in html source code and logout
  # (Sicherheitsprüfung hinzugefügt, falls Button nicht gefunden wird)
  logout_button = soup.find('a', {'id': 'logoutButton'})
  if logout_button and 'href' in logout_button.attrs:
    logout_url = BASE_URL + logout_button['href']
    logout(logout_url, cookie_request.cookies)

  # --- Rückgabe als normale Python-Liste (ersetzt 'jsonify') ---
  return units


# ----- Die Hilfsfunktionen bleiben unverändert -----

def parse_student_results(url, cookies):
  response = requests.get(url=url, cookies=cookies)
  student_result_soup = BeautifulSoup(response.content, "html.parser")
  table = student_result_soup.find("table", {"class": "students_results"})
  return [a['href'] for a in table.find_all("a", href=True)]


def parse_semester(url, cookies):
  semester_response = requests.get(url, cookies=cookies)
  semester_soup = BeautifulSoup(semester_response.content, 'html.parser')
  table = semester_soup.find("table", {"class": "list"})
  return [script.text.strip()[301:414] for script in table.find_all("script")]


def parse_unit(url, cookies):
  response = requests.get(url=BASE_URL + url, cookies=cookies)
  detail_soup = BeautifulSoup(response.content, "html.parser")
  h1 = detail_soup.find("h1").text.strip()
  table = detail_soup.find("table", {"class": "tb"})
  td = [td.text.strip() for td in table.find_all("td")]
  unit = {'name': h1.replace("\n", " ").replace("\r", ""), 'exams': []}
  # units have non uniform structure. Try to map based on total size.
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
  return unit


def logout(url, cookies):
  return requests.get(url=url, cookies=cookies).ok


# --- HINZUGEFÜGT: Anvil Server Uplink ---
# Dieser Teil wird benötigt, um das Skript als Server laufen zu lassen.
if __name__ == "__main__":
  # Ersetzen Sie dies mit Ihrem Anvil Uplink Key
  anvil.server.connect("DEIN_UPLINK_SCHLÜSSEL_HIER") 

  print("Verbunden mit Anvil. Warte auf Funktionsaufrufe...")
  anvil.server.wait_forever()


