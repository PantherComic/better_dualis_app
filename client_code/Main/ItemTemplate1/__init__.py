from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.server

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

  @property
  def item(self):
    return self._item

  @item.setter
  def item(self, value):
    self._item = value

    # --- KORREKTUR ---
    # Die festen Beschriftungen "Note:" und "CPs:" wurden entfernt.
    # Die Labels zeigen jetzt nur noch die reinen Daten an.

    # Stelle sicher, dass deine Labels im Designer 
    # (semester_label, name_label, grade_label, cp_label, status_label) heißen.

    self.semester_label.text = self._item.get('semester_name', '-') # <-- HINZUGEFÜGT
    self.name_label.text = self._item.get('name', 'N/A')
    self.grade_label.text = self._item.get('grade', '-')
    self.cp_label.text = self._item.get('cp', '-')
    self.status_label.text = self._item.get('status', 'N/A')