# Flask User Authentication API

This project is a user authentication API built using Flask, Flask-JWT-Extended, and MongoDB. It allows users to sign up and log in, managing their credentials securely using password hashing and JSON Web Tokens (JWT) for authentication.

## Features

- User Signup
- User Login
- Password Hashing for Security
- JWT for Access Control
- Error Handling
- CORS Support

## Technologies Used

- Flask
- Flask-JWT-Extended
- Flask-PyMongo
- MongoDB
- Werkzeug
- CORS
## Endpoints

### 1. User Signup
- **URL:** `/user/signup`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
    "name": "John Doe",
    "dob": "1990-01-01",
    "age": 34,
    "nationality": "American",
    "phone": "1234567890",
    "email": "john.doe@example.com",
    "password": "your_password"
  }

  
### 2. User login
- **URL:** `/user/login`
- **Method:** `POST`
- **Request Body:**
  ```json
  {
  "email": "john.doe@example.com",
  "password": "your_password"
  }



