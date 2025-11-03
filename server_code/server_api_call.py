import anvil.server

#!/usr/bin/python
import os
os.system('wget https://github.com/KarelZe/dualis/archive/master.zip')
os.system('unzip master.zip')
os.system('mv dualis-master dualis')
os.system('cd dualis')
os.system('make')


@anvil.server.callable
def api_call(name):
  curl -i -H "Content-Type: application/json" -X GET -d '{"user":"karel.zeman@dhbw-karlsruhe.de","password":"journeyToTheCenterOftheEarth"}' http://localhost:5000/dualis/api/v1.0/grades/
