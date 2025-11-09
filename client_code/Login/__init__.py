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

      # --- Debug-Verbesserungen ---
      # 1. Status-Label für Lade-Feedback nutzen
    self.status_label.text = "Einloggen und Noten abrufen... (Dies kann 5-10 Sekunden dauern)"
    # 2. Button deaktivieren, um doppelte Anfragen zu verhindern
    self.outlined_button_1.enabled = False

    try:
      grades_list = anvil.server.call('get_grades', user, password)

      # Altes Alert beibehalten, wenn es gewünscht ist, aber Label auch aktualisieren
      self.status_label.text = f"Erfolgreich! {len(grades_list)} Lerneinheiten gefunden."
      alert(f"Noten erfolgreich abgerufen: {len(grades_list)} Lerneinheiten gefunden.")

      # Hier Logik einfügen, um die Noten in der App anzuzeigen
      # z.B. open_form('NotenAnzeige', grades=grades_list)

    except anvil.server.PermissionDenied as e:
      # 3. Label für Fehler nutzen (besser als Alert)
      self.status_label.text = f"Login fehlgeschlagen: {e}"
    except Exception as e:
      # 4. Label für andere Fehler nutzen
      self.status_label.text = f"Ein Fehler ist aufgetreten: {e}"
    finally:
      # 5. Button in jedem Fall wieder aktivieren
      self.outlined_button_1.enabled = True