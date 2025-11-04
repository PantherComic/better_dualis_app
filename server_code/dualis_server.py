import anvil.server
import requests


@anvil.server.callable
def fetch_grades_from_dualis(username, password):
  if not username or not password:
    return None, "Benutzername und Passwort dürfen nicht leer sein."
  try:
    dualis = Dualis(username, password, cache=False)
    results_data = dualis.get_results()

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

    return grade_list, None

  except requests.exceptions.ConnectionError as e:
    return None, f"Verbindungsfehler: {e}"
  except Exception as e:
    return None, f"Fehler beim Abrufen der Daten: {e}"
