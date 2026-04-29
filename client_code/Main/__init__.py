from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import webbrowser
import re
from .ItemTemplate1 import ItemTemplate1

class Main(MainTemplate):
  def __init__(self, result_data=None, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)


    self.semester_dropdown.set_event_handler('change', self.semester_dropdown_change)

    self.all_grades_list = []

    if result_data:
      student_name = result_data.get('student_name', 'Student')
      self.name_display_label.text = f"Willkommen, {student_name}"

      self.all_grades_list = result_data.get('grades', [])

      self.populate_semester_dropdown()
      self.update_grades_display()

    else:
      self.name_display_label.text = "Keine Daten empfangen."
      self.grades_panel.items = []
      self.gpa_label.text = "N/A" 
      self.total_cp_label.text = "0"

    self.grades_panel.item_template = ItemTemplate1

  def abmelden_button_click(self, **event_args):
    open_form('Login')

  def dualis_link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")

  def sort_semester_key(self, semester_tuple):
    name = semester_tuple[0] 

    if name == "Alle Semester":
      return (9999, 9999) 

    match = re.search(r'\d{4}', name)
    year = int(match.group()) if match else 0

    if "WiSe" in name or "Winter" in name:
      season = 2
    elif "SoSe" in name or "Sommer" in name:
      season = 1
    else:
      season = 0 

    return (year, season)

  def populate_semester_dropdown(self, **event_args):
    semester_names = set(item['semester_name'] for item in self.all_grades_list if item.get('semester_name'))
    dropdown_items = [("Alle Semester", "ALL")]

    for name in semester_names:
      dropdown_items.append((name, name))

    # Liste wird chronologisch sortiert ("Alle Semester" auf Index 0, neuestes Semester auf Index 1)
    dropdown_items.sort(key=self.sort_semester_key, reverse=True)

    self.semester_dropdown.items = dropdown_items

    # NEU: Das neueste Semester als Standard auswählen (falls vorhanden)
    if len(dropdown_items) > 1:
      # dropdown_items[1] ist das neueste Semester. [1] greift auf den internen Wert zu.
      self.semester_dropdown.selected_value = dropdown_items[1][1]
    else:
      self.semester_dropdown.selected_value = "ALL"

  def semester_dropdown_change(self, **event_args):
    self.update_grades_display()

  def calculate_gpa(self, grades_to_calc):
    total_weighted_grade = 0.0
    total_cp = 0.0

    for item in grades_to_calc:
      grade_str = item.get('grade')
      cp_str = item.get('cp')
      status = item.get('status', '').lower()

      if 'bestanden' in status or status == 'prüfung bestanden':
        try:
          grade = float(grade_str.replace(',', '.'))
          cp = float(cp_str.replace(',', '.'))

          if cp > 0 and grade > 0:
            total_weighted_grade += (grade * cp)
            total_cp += cp

        except (ValueError, TypeError, AttributeError):
          continue

    if total_cp > 0:
      gpa = total_weighted_grade / total_cp
      return (gpa, total_cp)
    else:
      return (None, 0) # Gibt None (für N/A) und 0 CPs zurück

  def update_grades_display(self, **event_args):
    selected_semester = self.semester_dropdown.selected_value

    display_list = []

    if selected_semester == "ALL":
      filtered_list = self.all_grades_list
    else:
      filtered_list = [
        item for item in self.all_grades_list 
        if item.get('semester_name') == selected_semester
      ]

    for item in filtered_list:
      exam = item.get('exams', [{}])[0]
      display_list.append({
        'semester_name': item.get('semester_name', '-'),
        'name': item.get('name', 'N/A'),
        'grade': exam.get('grade', '-'),
        'status': exam.get('status', 'N/A'),
        'cp': exam.get('cp', '-')
      })

    self.grades_panel.items = display_list

    # GPA Anzegen
    gpa_value, cp_value = self.calculate_gpa(display_list)

    try:
      if gpa_value is not None:
        self.gpa_label.text = f"{gpa_value:.2f}"
      else:
        self.gpa_label.text = "N/A"

      self.total_cp_label.text = f"{cp_value:.0f}"

      self.gpa_label.visible = True
      self.total_cp_label.visible = True

    except AttributeError as e:
      print(f"WARNUNG: Label nicht im Main-Formular gefunden (z.B. 'gpa_label' oder 'total_cp_label'). Fehler: {e}")