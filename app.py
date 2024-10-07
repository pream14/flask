from flask import Flask, jsonify, request,send_from_directory
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import traceback
import datetime
from dotenv import load_dotenv
from datetime import datetime, timezone
from datetime import timedelta  

import os
import urllib.parse
load_dotenv()


# Ensure that MONGO_URI is being correctly pulled from the .env file


app = Flask(__name__)
CORS(app)

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
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

import os

@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    try:
        # Get the form data
        full_name = request.form.get('fullName')
        email = request.form.get('email')
        phone = request.form.get('phone')
        cover_letter = request.form.get('coverLetter')
        resume_file = request.files.get('resume')

        # Validate form data
        if not full_name or not email or not phone or not resume_file:
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate file type (only accept PDFs)
        if not resume_file.filename.endswith('.pdf'):
            return jsonify({'error': 'Only PDF resumes are allowed'}), 400

        # Check if user exists
        user = mongo.db.user.find_one({'email': email})

        if user:
            user_id = user['_id']
        else:
            # If user does not exist, create a new user
            new_user = {
                'email': email,
                'full_name': full_name,
                'phone': phone
            }
            user_id = mongo.db.user.insert_one(new_user).inserted_id

        # Ensure the uploads directory exists
        uploads_dir = './uploads'
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)

        # Handle potential duplicate filenames by appending a timestamp
        filename = f"{str(user_id)}_{int(datetime.now().timestamp())}.pdf"
        resume_file_path = os.path.join(uploads_dir, filename)

        # Save the resume file
        resume_file.save(resume_file_path)

        # Save resume data in the 'resume' collection
        resume_data = {
            'user_id': user_id,
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'cover_letter': cover_letter,
            'resume_filename': filename,
            'uploaded_at': datetime.now(timezone.utc)
        }
        mongo.db.resume.insert_one(resume_data)

        return jsonify({'message': 'Resume uploaded successfully', 'user_id': str(user_id)})

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(traceback.format_exc())
        return error_stack(str(e))

@app.route('/resume/<filename>', methods=['GET'])
def get_resume(filename):
    try:
        # Define the upload directory where resumes are stored
        uploads_dir = './uploads'
        
        # Send the requested file from the uploads directory
        return send_from_directory(uploads_dir, filename, as_attachment=True)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'File not found or some other error occurred'}), 404


# Route to get the resume filename by user's email
@app.route('/get-resume-by-email', methods=['GET'])
def get_resume_by_email():
    try:
        email = request.args.get('email')

        # Find the resume associated with the user's email
        resume_data = mongo.db.resume.find_one({'email': email})

        if not resume_data:
            return jsonify({'error': 'Resume not found for this email'}), 404

        # Return the filename to be used for downloading
        filename = resume_data['resume_filename']
        return jsonify({'filename': filename})

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': 'An error occurred'}), 500




if __name__ == "__main__":
    app.run(debug=True)
