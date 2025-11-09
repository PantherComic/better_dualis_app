from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import webbrowser
from .ItemTemplate1 import ItemTemplate1 # <-- DIESE ZEILE HINZUFÜGEN

class Main(MainTemplate):
  def __init__(self, grades_list=None, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Setze das ItemTemplate für das RepeatingPanel
    self.grades_panel.item_template = ItemTemplate1 

    display_list = []
    if grades_list:
      # --- DATENAUFBEREITUNG ("FLACH KLOPFEN") ---
      # Wir bereiten die Daten so auf, dass ItemTemplate1
      # sie im 'item'-Setter verarbeiten kann.

      for item in grades_list:
        # Nimm die erste Prüfung aus der 'exams'-Liste (oder ein leeres Dict)
        first_exam = item.get('exams', [{}])[0] 

        # --- KORREKTUR: Schlüsselnamen an ItemTemplate1 angepasst ---
        # ItemTemplate1 erwartet 'name', 'grade', 'status' und 'cp'.

        display_list.append({
          'name': item.get('name', 'N/A'),
          'grade': first_exam.get('grade', 'N/A'),
          'status': first_exam.get('status', 'N/A'),
          'cp': first_exam.get('cp', 'N/A') # <-- KORREKTUR: Hinzugefügt
        })

      self.grades_panel.items = display_list
    else:
      # Fallback, falls die Seite direkt ohne Daten geladen wird
      self.grades_panel.items = []
      alert("Keine Noten zum Anzeigen gefunden.")

  def abmelden_button_click(self, **event_args):
    open_form('Login')

  def link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")