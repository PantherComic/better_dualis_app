from ._anvil_designer import LoginTemplate
from anvil import *
import anvil.server
import webbrowser

class Login(LoginTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    # --- DataGrid-Spalten-Definition entfernt ---

  def link_1_click(self, **event_args):
    # Öffnet die Dualis-Seite in einem neuen Tab
    webbrowser.open("https://dualis.dhbw.de/")

  def outlined_button_1_click(self, **event_args):
    user = self.user_box.text
    password = self.password_box.text

    if not user or not password:
      self.status_label.text = "Bitte geben Sie Benutzername und Passwort ein."
      self.status_label.foreground = "#FF0000" # Rot für Fehler
      return

      # --- UI für Ladevorgang ---
    self.status_label.text = "Melde an und lade Noten... (Dies kann einige Sekunden dauern)"
    self.status_label.foreground = "#000000" # Standardfarbe
    self.outlined_button_1.enabled = False # Button deaktivieren

    # --- Referenz auf 'self.progress_bar' ENTFERNT ---

    try:
      # Server-Funktion aufrufen
      grades_list = anvil.server.call('get_grades', user, password)

      # --- ERFOLGSFALL (GEÄNDERT) ---
      # Öffne das Main-Formular und übergib die Rohdaten der Noten
      open_form('Main', grades_list=grades_list)

    except anvil.server.PermissionDenied as e:
      # Login fehlgeschlagen (vom Server ausgelöst)
      self.status_label.text = f"Login fehlgeschlagen: {e}"
      self.status_label.foreground = "#FF0000"
      # Wichtig: UI bei Fehler wieder aktivieren
      self.outlined_button_1.enabled = True
    except Exception as e:
      # Alle anderen Fehler (Netzwerk, 403, 500, etc.)
      self.status_label.text = f"Ein unerwarteter Fehler ist aufgetreten: {e}"
      self.status_label.foreground = "#FF0000"
      # Wichtig: UI bei Fehler wieder aktivieren
      self.outlined_button_1.enabled = True