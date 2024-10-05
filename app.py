from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import traceback
import datetime
from dotenv import load_dotenv
import os
import urllib.parse
load_dotenv()


# Ensure that MONGO_URI is being correctly pulled from the .env file


app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
username = os.getenv('MONGO_USERNAME')  # Define MONGO_USERNAME in your .env
password = os.getenv('MONGO_PASSWORD')  # Define MONGO_PASSWORD in your .env

# Encode the username and password
encoded_username = urllib.parse.quote_plus(username)
encoded_password = urllib.parse.quote_plus(password)

# Construct the Mongo URI
mongo_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@cluster0.vtghi.mongodb.net/dev"


app.config['MONGO_URI'] = mongo_uri

print(f"Mongo URI: {app.config['MONGO_URI']}")


jwt = JWTManager(app)
mongo = PyMongo(app)

def error_stack(error):
    stack_trace = traceback.format_exc()
    response = {
        'error': error,
        'stack_trace': stack_trace
    }
    return jsonify(response), 500

@app.route('/user/signup', methods=['POST'])
def adduser():
    try:
        _json = request.json
        new_user = {
            'name': _json.get('name'),
            'dob': _json.get('dob'),
            'age': _json.get('age'),
            'nationality': _json.get('nationality'),
            'phone': _json.get('phone'),
            'email': _json.get('email'),
            'password': _json.get('password')
        }

        if not new_user['password']:
            return jsonify({'error': 'Password is required'}), 400

        new_user['password'] = generate_password_hash(new_user['password'])

        existing_user = mongo.db.user.find_one({'email': new_user['email']})
        if existing_user:
            return jsonify({'error': 'User with email already exists'}), 400

        mongo.db.user.insert_one(new_user)
        access_token = create_access_token(identity=new_user['email'])
        return jsonify({"message": "User added successfully", "access_token": access_token}), 200

    except Exception as e:
        print("Error occurred:", str(e))
        print(traceback.format_exc())
        return error_stack(str(e))

@app.route('/test_db', methods=['GET'])
def test_db():
    try:
        mongo.db.command('ping')  # A simple command to check MongoDB connection
        return jsonify({'message': 'Database connection is successful'}), 200
    except Exception as e:
        return error_stack(str(e))


@app.route('/user/login', methods=['POST'])
def login():
    try:
        email = request.json.get('email')
        password = request.json.get('password')

        user = mongo.db.user.find_one({'email': email})

        if user and check_password_hash(user['password'], password):
            access_token = create_access_token(identity=email)
            return jsonify({'access_token': access_token}), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return error_stack(str(e))

@app.errorhandler(Exception)
def handle_exception(e):
    return error_stack(str(e))

if __name__ == "__main__":
    app.run(debug=True)
