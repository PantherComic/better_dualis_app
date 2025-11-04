from ._anvil_designer import LoginTemplate
from anvil import *
import anvil.server
import webbrowser

class Login(LoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
  

  def link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")



  def outlined_button_1_click(self, **event_args):
    user = self.user_box.text
    password = self.password_box.text

    if not user or not password:
      self.status_label.text = "Bitte geben Sie Benutzername und Passwort ein."
      return

    try:
      grades_list = anvil.server.call('get_grades', user, password)
      print("Noten erfolgreich abgerufen:", grades_list)
      # Zeigen Sie die Noten in Ihrer App an
    except anvil.server.PermissionDenied as e:
     # Dieser Fehler wird ausgelöst, wenn der Login fehlschlägt
      alert(f"Login fehlgeschlagen: {e}")
    except Exception as e:
      # Fängt andere Fehler ab (z.B. Verbindungsfehler)
      alert(f"Ein Fehler ist aufgetreten: {e}")
