from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import webbrowser


class Main(MainTemplate):
  def __init__(self, grades_list=None, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.grades_panel.item_template = ItemTemplate1

    if grades_list:
      self.grades_panel.items = grades_list
    else:
      self.grades_panel.items = []
      alert("Keine Noten zum Anzeigen gefunden.")


    

  def abmelden_button_click(self, **event_args):
    open_form('Login')
  
  def link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")

 
