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
    # Setzen der Label-Texte basierend auf den Daten
    self.course_name_label.text = self._item.get('name', 'N/A')
    self.grade_label.text = f"Note: {self._item.get('grade', '-')}"
    self.cp_label.text = f"CPs: {self._item.get('cp', '-')}"
    # Any code you write here will run before the form opens.
