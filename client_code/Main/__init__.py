from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import webbrowser
from .ItemTemplate1 import ItemTemplate1

class Main(MainTemplate):
  def __init__(self, result_data=None, **properties):
    self.init_components(**properties)
    self.grades_panel.item_template = ItemTemplate1 
    display_list = []

    if result_data:
      grades_list = result_data.get('grades', [])
      student_name = result_data.get('student_name', 'Unbekannt')

      try:
        self.name_display_label.text = f"Willkommen, {student_name}"
      except AttributeError:
        print("WARNUNG: Label 'name_display_label' nicht im Main-Formular gefunden.")

      for item in grades_list:
        first_exam = item.get('exams', [{}])[0] 
        display_list.append({
          'semester_name': item.get('semester_name', 'N/A'),
          'name': item.get('name', 'N/A'),
          'grade': first_exam.get('grade', 'N/A'),
          'status': first_exam.get('status', 'N/A'),
          'cp': first_exam.get('cp', 'N/A') 
        })

      self.grades_panel.items = display_list
    else:
      self.grades_panel.items = []
      try:
        self.name_display_label.text = "Willkommen"
      except AttributeError:
        pass
      alert("Keine Noten zum Anzeigen gefunden.")

  def abmelden_button_click(self, **event_args):
    open_form('Login')

  def dualis_link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")