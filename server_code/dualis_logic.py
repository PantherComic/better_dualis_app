"""
DIES IST DER KOPIERTE CODE AUS DEM 'KarelZe/dualis' REPOSITORY.
Original: https://github.com/KarelZe/dualis/blob/main/dualis/dualis.py
(Lizenz: MIT)

Dieser Code wird direkt in Ihr Anvil-Projekt eingefügt,
um die fehlerhafte Paketinstallation zu umgehen.
"""

import datetime
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Optional

# --- Constants ---
DEFAULT_SEMESTER_ID = "53"  # TODO: this needs to be updated or detected
LOGIN_URL = "https://dualis.dhbw.de/scripts/mgrqispi.dll"
DEFAULT_ARGS = {
  "APPNAME": "CampusNet",
  "PRGNAME": "LOGINCHECK",
  "ARGUMENTS": "clino,usrname,pass,menuno,menu_type,browser,platform",
  "clino": "000000000000001",
  "menuno": "000324",
  "menu_type": "classic",
  "browser": "",
  "platform": "",
}
DEFAULT_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36"
}
SESSION_NAME = "default"
CACHE_DIR = "cache"

# --- Helper classes ---
class Result:
  def __init__(self, data: List[str]):
    self.number: str = data[0]
    self.name: str = data[1]
    self.semester: str = data[2]
    self.grade: str = data[3]
    self.status: str = data[4]
    self.cp: str = data[5]
    self.attempt: str = data[6]
    self.date: Optional[datetime.date] = (
      datetime.datetime.strptime(data[7], "%d.%m.%Y").date() if data[7] else None
    )
    self.ects_grade: str = data[8]
    self.type: str = data[9]

  def __str__(self):
    return f"{self.name} ({self.number}): {self.grade} ({self.cp} CP)"


class Semester:
  def __init__(self, data: List[str]):
    self.id: str = re.search(r"submitform\('(.+?)'\)", data[0]).group(1)
    self.name: str = re.search(r"ref=\"(.*?)\"", data[0]).group(1).split(";")[-1]
    self.courses: List[SemesterCourse] = []

  def __str__(self):
    return f"{self.name} ({self.id})"


class SemesterCourse:
  def __init__(self, data: List[str]):
    self.name: str = data[0]
    self.number: str = data[1]
    self.cp_a: str = data[2]
    self.cp_b: str = data[3]
    self.grade: str = data[4]

  def __str__(self):
    return f"{self.name} ({self.number}): {self.grade} ({self.cp_a}/{self.cp_b} CP)"


class Cache:
  def __init__(self, session_name: str, cache: bool):
    self.path = os.path.join(CACHE_DIR, f"{session_name}.json")
    self.cache = cache
    if cache and not os.path.exists(CACHE_DIR):
      os.mkdir(CACHE_DIR)

  def read(self) -> Optional[dict]:
    if self.cache and os.path.exists(self.path):
      with open(self.path, "r") as f:
        return json.load(f)
    return None

  def write(self, data: dict):
    if self.cache:
      with open(self.path, "w") as f:
        json.dump(data, f)


# --- Main class ---
class Dualis:
  def __init__(self, username, password, session_name=SESSION_NAME, cache=True):
    self.username = username
    self.password = password
    self.session = requests.Session()
    self.session.headers.update(DEFAULT_HEADERS)
    self.cache = Cache(session_name, cache)
    self.refresh_args()

  def refresh_args(self):
    """Refreshes arguments by sending new login request"""
    data = self.cache.read()
    if data:
      self.args = data
      self.session.cookies.set("cnsc", self.args["cnsc"])
    else:
      self.args = DEFAULT_ARGS
      self.args["usrname"] = self.username
      self.args["pass"] = self.password
      r = self.session.get(LOGIN_URL, params=self.args)
      self.args = self.parse_refresh_args(r.text)
      self.cache.write(self.args)

  def parse_refresh_args(self, html: str) -> dict:
    """Parses refresh arguments from html"""
    soup = BeautifulSoup(html, "html.parser")
    try:
      refresh = soup.find("meta", {"http-equiv": "refresh"})["content"]
      url = refresh.split("url=")[1]
      args = dict(x.split("=") for x in url.split("?")[1].split("&"))
      args["cnsc"] = self.session.cookies.get_dict()["cnsc"]
      return args
    except TypeError:
      raise Exception("Login failed. Check username and password.")

  def get_semesters(self) -> List[Semester]:
    """Returns a list of semesters"""
    r = self.session.get(
      LOGIN_URL,
      params={
        "APPNAME": "CampusNet",
        "PRGNAME": "STUDENT_RESULT",
        "ARGUMENTS": f"-N{self.args['arg']},-N{DEFAULT_SEMESTER_ID}",
      },
    )
    soup = BeautifulSoup(r.text, "html.parser")
    semester_list = soup.find("select", {"id": "semester"}).find_all("option")
    semesters = [
      Semester([str(s)]) for s in semester_list if re.search(r"submitform", str(s))
    ]
    return semesters

  def get_semester_courses(self, semester_id: str) -> List[SemesterCourse]:
    """Returns a list of courses for a given semester"""
    r = self.session.get(
      LOGIN_URL,
      params={
        "APPNAME": "CampusNet",
        "PRGNAME": "STUDENT_RESULT",
        "ARGUMENTS": f"-N{self.args['arg']},-N{semester_id}",
      },
    )
    soup = BeautifulSoup(r.text, "html.parser")
    course_list = soup.find_all("tr", {"class": ["tbdata", "tbdata_b"]})
    courses = [
      SemesterCourse([c.text for c in course.find_all("td")])
      for course in course_list
    ]
    return courses

  def get_results(self) -> List[Result]:
    """Returns a list of results"""
    r = self.session.get(
      LOGIN_URL,
      params={
        "APPNAME": "CampusNet",
        "PRGNAME": "RESULTS",
        "ARGUMENTS": f"-N{self.args['arg']}",
      },
    )
    soup = BeautifulSoup(r.text, "html.parser")
    result_list = soup.find_all("tr", {"class": ["tbdata", "tbdata_b"]})
    results = [
      Result([re.sub(r"\s+", " ", c.text.strip()) for c in result.find_all("td")])
      for result in result_list
    ]
    return results

  def get_gpa(self) -> float:
    """Returns the grade point average"""
    r = self.session.get(
      LOGIN_URL,
      params={
        "APPNAME": "CampusNet",
        "PRGNAME": "RESULTS",
        "ARGUMENTS": f"-N{self.args['arg']}",
      },
    )
    soup = BeautifulSoup(r.text, "html.parser")
    gpa = soup.find("h2").text.split(" ")[-1]
    return float(gpa.replace(",", "."))
