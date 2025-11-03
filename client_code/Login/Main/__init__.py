from ._anvil_designer import MainTemplate
from anvil import *
import anvil.server
import webbrowser


class Main(MainTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def link_1_click(self, **event_args):
    webbrowser.open("https://dualis.dhbw.de/")
