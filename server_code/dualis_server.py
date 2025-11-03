import anvil.server
from .dualis_logic import Dualis
import requests

@anvil.server.callable
def fetch_grades_from_dualis(username, password):
  """
    Meldet sich bei Dualis an und ruft Noten und CP ab.
    Gibt eine Liste von Diktionären zurück, z.B.:
    [{'name': 'Mathe 1', 'grade': '1.3', 'cp': '5.0', ...}, ...]
    """
  if not username or not password:
    return None, "Benutzername und Passwort dürfen nicht leer sein."

  try:
    # 1. Anmelden und Session erstellen
    # 'cache=False' ist WICHTIG, da Anvil-Server "stateless" sind
    # und wir keine lokalen Dateien speichern wollen.
    dualis = Dualis(username, password, cache=False)

    # 2. Daten abrufen
    results_data = dualis.get_results()

    # 3. Daten für den Client aufbereiten
    # 'results_data' ist eine Liste von Objekten. Wir wandeln sie
    # in eine Liste von Diktionären um, die Anvil leicht versteht.

    grade_list = []
    for course in results_data:
      grade_list.append({
        'name': course.name,
        'grade': course.grade,
        'cp': course.cp,
        'attempt': course.attempt,
        'date': course.date.strftime('%Y-%m-%d') if course.date else None,
        'ects_grade': course.ects_grade,
        'number': course.number,
        'semester': course.semester,
        'status': course.status,
        'type': course.type
      })

    return grade_list, None # Daten zurückgeben, kein Fehler

  except requests.exceptions.ConnectionError as e:
    # Spezieller Fehler, falls Dualis nicht erreichbar ist
    return None, f"Verbindungsfehler: {e}"
  except Exception as e:
    # Allgemeiner Fehler (z.B. falsches Passwort)
    # Wir geben den Fehlertext als String zurück
    return None, f"Fehler beim Abrufen der Daten: {e}"
