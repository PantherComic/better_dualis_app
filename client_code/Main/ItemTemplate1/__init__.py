from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.server

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # --- KORREKTUR FÜR MOBIL-ABSTAND (Versuch 3) ---

    # Setzt den Abstand unter diesem gesamten Element
    self.spacing_below = "medium"

    # Weist dem Formular eine Standard-Rolle zu.
    # "outlined" zeichnet einen konsistenten Rahmen,
    # was das Layout-Problem beheben sollte.
    self.role = "outlined" 

    # Manueller Border-Code wurde entfernt
    # self.border = ...
    # self.border_color = ...

  @property
  def item(self):
    return self._item

  @item.setter
  def item(self, value):
    self._item = value

    # Stelle sicher, dass deine Labels im Designer 
    # (semester_label, name_label, grade_label, cp_label, status_label) heißen.

    self.semester_label.text = self._item.get('semester_name', '-')
    self.name_label.text = self._item.get('name', 'N/A')
    self.grade_label.text = self._item.get('grade', '-')
    self.cp_label.text = self._item.get('cp', '-')

    # --- KORREKTUR FÜR LEERE LABELS ---
    # Stellt sicher, dass das Status-Label immer Inhalt hat,
    # damit die Höhe konsistent bleibt.
    status_text = self._item.get('status', '-') # Holt den Status

    # Wenn der Text leer ist (oder nur Leerzeichen), setze "noch nicht bestanden"
    if not status_text or status_text.isspace():
      self.status_label.text = "noch nicht bestanden" # <-- GEÄNDERT
    else:
      self.status_label.text = status_text
      # --- ENDE KORREKTUR -