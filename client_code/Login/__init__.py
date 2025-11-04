from ._anvil_designer import LoginTemplate
from anvil import *
import anvil.server
import webbrowser
from .Main import Main
from .Main.ItemTemplate1 import ItemTemplate1

class Login(LoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
  

  def link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")



  def outlined_button_1_click(self, **event_args):
    username = self.username_box.text
    password = self.password_box.text

    if not username or not password:
      self.status_label.text = "Bitte geben Sie Benutzername und Passwort ein."
      return

    try:
      grades_data, error_message = anvil.server.call('fetch_grades_from_dualis', username, password)
  
      if error_message:
        self.status_label.text = f"Fehler: {error_message}"
      elif grades_data:
        open_form('Login.Main', grades_list=grades_data)
      else:
        self.status_label.text = "Keine Daten empfangen."
  
    except Exception as e:
      self.status_label.text = f"Ein unerwarteter Client-Fehler ist aufgetreten: {e}"
