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
    # Dieser Code wird jetzt ausgeführt und weist die Daten 
    # den Labels im Designer zu.

    # Wir greifen auf die Daten zu, die Main.py uns gibt:
    # self._item['name'], self._item['grade'], etc.

    # Wir weisen sie den Labels in DIESEM Template zu.
    # Ich gehe davon aus, dass deine Labels so heißen:
    # name_label, grade_label, cp_label, status_label

    # Wenn deine Labels anders heißen, passe die Namen hier an
    # (z.B. self.meine_note_label.text = ...)

    self.name_label.text = self._item.get('name', 'N/A')
    self.grade_label.text = f"Note: {self._item.get('grade', '-')}"
    self.cp_label.text = f"CPs: {self._item.get('cp', '-')}"
    self.status_label.text = self._item.get('status', 'N/A')