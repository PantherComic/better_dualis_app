import anvil.server

@anvil.server.callable
def api_call(name):
  $ curl -i -H "Content-Type: application/json" -X GET -d '{"user":"karel.zeman@dhbw-karlsruhe.de","password":"journeyToTheCenterOftheEarth"}' http://localhost:5000/dualis/api/v1.0/grades/
