from ._anvil_designer import ItemTemplate1Template
from anvil import *
import anvil.server

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    self.spacing_below = "medium"
    self.role = "outlined" 

  @property
  def item(self):
    return self._item

  @item.setter
  def item(self, value):
    self._item = value

    self.semester_label.text = self._item.get('semester_name', '-')
    self.name_label.text = self._item.get('name', 'N/A')
    self.grade_label.text = self._item.get('grade', '-')
    self.cp_label.text = self._item.get('cp', '-')

    status_text = self._item.get('status', '-') # Holt den Status

    # Wenn der Text leer ist (oder nur Leerzeichen), setze "noch nicht bestanden"
    if not status_text or status_text.isspace():
      self.status_label.text = "noch nicht bestanden"
    else:
      self.status_label.text = status_text
