import os
import cloudant
from flask import Flask, jsonify, abort, request, make_response
import json

# Read port selected by the cloud for our application
PORT = int(os.getenv('VCAP_APP_PORT', 8000))

app = Flask(__name__)

if 'VCAP_SERVICES' in os.environ:
    cloudantInfo = json.loads(os.environ['VCAP_SERVICES'])['cloudantNoSQLDB'][0]
#we are local
else:
    with open('.env.vcap_services.json') as configFile:
        cloudantInfo = json.load(configFile)['VCAP_SERVICES']['cloudantNoSQLDB'][0]

username = cloudantInfo["credentials"]["username"]
password = cloudantInfo["credentials"]["password"]

account = cloudant.Account(username)
login = account.login(username, password)
assert login.status_code == 200

# create the database object
db = account.database('calls')

databases = json.loads(account.all_dbs().content)
if 'calls' not in databases:
    # now, create the database on the server
    response = db.put()
    print response.json()


# @app.route('/')
# def hello_world():
#     return 'Hello World!'


@app.route('/api/v1/calls', methods=['GET'])
def getCalls():
    response = db.all_docs().get(params={'include_docs': True})

    if response.status_code != 200:
        abort(response.status_code)

    rows = json.loads(response.content)['rows']

    docs = map(lambda row: row['doc'], rows)

    return jsonify({'calls': docs}), response.status_code


@app.route('/api/v1/calls', methods=['POST'])
def createCall():
    if not request.json:
        abort(400)

    call = {
        'name': request.json['name'],
        'eventhost': request.json['eventhost'],
        'time': request.json['time'],
        'address': request.json['address'],
    }

    response = db.document('', params=call).post()

    return make_response(response.content, response.status_code, {'Content-Type': 'application/json'})


@app.route('/api/v1/calls/<string:id>', methods=['GET'])
def getCall(id):
    response = db.get(id)

    if response.status_code != 200:
        abort(response.status_code)

    return make_response(response.content, response.status_code, {'Content-Type': 'application/json'})


@app.route('/api/v1/calls/<string:id>', methods=['PUT'])
def updateCall(id):
    if not request.json:
        abort(400)

    document = db.document(id)

    response = document.merge(request.json)

    return '', response.status_code


@app.route('/api/v1/calls/<string:id>', methods=['DELETE'])
def deleteCall(id):
    response = db.get(id)

    if response.status_code != 200:
        abort(response.status_code)

    doc = json.loads(response.content)

    response = db.delete(id, params={'rev': doc['_rev']})

    return '', response.status_code


if __name__ == '__main__':
    print("Start serving at port %i" % PORT)
    app.run('', PORT, debug=True)
