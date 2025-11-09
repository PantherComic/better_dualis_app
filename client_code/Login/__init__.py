from ._anvil_designer import LoginTemplate
from anvil import *
import anvil.server
import webbrowser

class Login(LoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

  def dualis_link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")

  def outlined_button_1_click(self, **event_args):
    user = self.user_box.text
    password = self.password_box.text

    if not user or not password:
      self.status_label.text = "Bitte geben Sie Benutzername und Passwort ein."
      self.status_label.foreground = "#FF0000" 
      return

    self.status_label.text = "Melde an und lade Noten... (Dies kann einige Sekunden dauern)"
    self.status_label.foreground = "#000000" 
    self.outlined_button_1.enabled = False 

    try:
      result_data = anvil.server.call('get_grades', user, password)
      open_form('Main', result_data=result_data)

    except anvil.server.PermissionDenied as e:
      self.status_label.text = f"Login fehlgeschlagen: {e}"
      self.status_label.foreground = "#FF0000"
      self.outlined_button_1.enabled = True
    except Exception as e:
      self.status_label.text = f"Ein unerwarteter Fehler ist aufgetreten: {e}"
      self.status_label.foreground = "#FF0000"
      self.outlined_button_1.enabled = True