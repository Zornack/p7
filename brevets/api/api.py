# Streaming Service

from flask import Flask
from flask_restful import Resource, Api
import os
import flask
from flask_restful import Resource, Api
from flask import Flask, redirect, url_for, request, render_template, make_response
import pymongo
from pymongo import MongoClient
import arrow  # Replacement for datetime, based on moment.js
import json
from bson import json_util

from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, \
                                BadSignature, SignatureExpired)

import logging

from passlib.hash import sha256_crypt as pwd_context

app = Flask(__name__)
api = Api(app)

## to do: make secret key
SECRET_KEY = "asecretkey"

client = MongoClient('mongodb://' + os.environ['MONGODB_HOSTNAME'], 27017)
db = client.controls
auth = client.users

def generate_auth_token(userID, expiration=600):
   s = Serializer(SECRET_KEY, expires_in=expiration)
   return s.dumps({'id': userID})

def verify_auth_token(token):
    s = Serializer(SECRET_KEY)
    verified = False
    try:
        if auth.users.find(s.loads(token)) != None:
             verified = True
    except SignatureExpired:
        return False    # Valid token, but expired
    except BadSignature:
        return False    # invalid token
    return verified

class token(Resource):
    def get(self):
        username = request.args.get('username')
        password = request.args.get('password')
        if password == None:
            return make_response("No password.", 401)
        if username == None:
            return make_repsonse("No username.", 401)
        if auth.users.find_one({'username':username}) == None:
            return make_response("That user does not exist.", 401)
        hashed = auth.users.find_one({'username': username})['password']
        if password != hashed:
            return make_response(json.dumps("Incorrect password."), 401)
        id = auth.users.find_one({'username': username})['id']
        ##from bytes to string: https://stackoverflow.com/questions/606191/convert-bytes-to-a-string
        token = generate_auth_token(auth.users.find_one({'username': username})['id']).decode("utf-8")
        return make_response(json.dumps({'id': id, 'token': token, 'duration': 600}), 200)


class register(Resource):
    def post(self):
        username = request.form.get('username', type = str)
        password = request.form.get('password', type = str)
        if password == None:
            return make_response("Your password is too short.", 400)
        if username == None:
            return make_repsonse("Your username is too short.", 400)
        if auth.users.find_one({'username':username}) != None:
            return make_response("That username is taken.", 400)
        id = auth.users.count() + 1
        newUser = {'id':id, 'username':username, 'password':password}
        auth.users.insert_one(newUser)
        newUser = json.dumps(newUser, default=str)
        return make_response(newUser, 201)

class listAll(Resource):
    def get(self, format=None):
        token = request.args.get('token')
        if verify_auth_token(token) == False:
            return make_response("Token invalid. Please log in.", 401)
        k = request.args.get('top', default=-1, type=int)
        if k <= 0:
            k = None
        if format == None:
            format = "json"
        if format != "csv" and format != "json":
            return make_response(format + " is not a suported format.")
        allArr = []
        for things in db.controls.find({}, {"_id": 0, "km": 0})[:k]:
            allArr.append(things)
        if format == "json":
            allJson = {}
            for x in range(len(allArr)):
                 allJson[x+1] = allArr[x]
            return allJson
        if format == "csv":
            if len(allArr) == 0:
                return ""
            head = list(allArr[0].keys())
            values = ""
            for things in allArr:
                values = values + ','.join(list(things.values()))
                values = values + "\n"
            return (",".join(head) + "\n" + values[:-1])


class listOpenOnly(Resource):
        def get(self, format=None):
            token = request.args.get('token')
            if verify_auth_token(token) == False:
                return make_response("Token invalid. Please log in.", 401)
            k = request.args.get('top', default=-1, type=int)
            if k <= 0:
                k = None
            if format == None:
                format = "json"
            if format != "csv" and format != "json":
                return make_response(format + " is not a suported format.")
            openArr = []
            for things in db.controls.find({}, {"_id": 0, "km": 0, "close": 0})[:k]:
                openArr.append(things)
            if format == "json":
                openJson = {}
                for x in range(len(openArr)):
                    openJson[x + 1] = openArr[x]
                return openJson
            if format == "csv":
                if len(openArr) == 0:
                    return ""
                head = list(openArr[0].keys())
                values = ""
                for things in openArr:
                    values = values + ','.join(list(things.values()))
                    values = values + "\n"
                return (",".join(head) + "\n" + values[:-1])

class listCloseOnly(Resource):
    def get(self, format = None):
        token = request.args.get('token')
        if verify_auth_token(token) == False:
            return make_response("Token invalid. Please log in.", 401)
        k = request.args.get('top', default=-1, type=int)
        if k <= 0:
            k = None
        if format == None:
            format = "json"
        if format != "csv" and format != "json":
            return make_response(format + " is not a suported format.")
        closeArr = []
        for things in db.controls.find({}, {"_id": 0,"km":0,"open":0})[:k]:
             closeArr.append(things)
        if format == "json":
            closeJson = {}
            for x in range(len(closeArr)):
                closeJson[x + 1] = closeArr[x]
            return closeJson
        if format == "csv":
            if len(closeArr) == 0:
                return ""
            head = list(closeArr[0].keys())
            values = ""
            for things in closeArr:
                values = values + ','.join(list(things.values()))
                values = values + "\n"
            return (",".join(head) + "\n" + values[:-1])

# Create routes
# Another way, without decorators
api.add_resource(listAll, '/listAll/<string:format>', '/listAll', '/listAll/')
api.add_resource(listOpenOnly, '/listOpenOnly/<string:format>', '/listOpenOnly','/listOpenOnly/')
api.add_resource(listCloseOnly, '/listCloseOnly/<string:format>', '/listCloseOnly','/listCloseOnly/')
api.add_resource(register, '/register')
api.add_resource(token, '/token')

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
