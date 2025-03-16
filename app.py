from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message
from pymongo import MongoClient
import secrets
import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication
bcrypt = Bcrypt(app)

# Configure JWT
app.config["JWT_SECRET_KEY"] = "supersecretkey"  # Change this in production
jwt = JWTManager(app)

# Configure Flask-Mail
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "trygeneralusage@gmail.com"  # Replace with your email
app.config["MAIL_PASSWORD"] = "itveondvcywplqrf"  # Use App Password if using Gmail
app.config["MAIL_DEFAULT_SENDER"] = "trygeneralusage@gmail.com"

mail = Mail(app)

# Configure MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["user_database"]
users_collection = db["users"]
questions_collection = db["questions"]
counters_collection = db["counters"]


# ------------------ Function to Get Next Auto-Incremented ID ------------------
def get_next_question_id():
    counter = counters_collection.find_one_and_update(
        {"_id": "question_id"},
        {"$inc": {"sequence_value": 1}},  # Increment sequence_value by 1
        upsert=True,
        return_document=True
    )
    return counter["sequence_value"]


# ------------------ Add Question API ------------------
@app.route("/add-question", methods=["POST"])
def add_question():
    data = request.json

    # Validate required fields
    if not all(key in data for key in ["question", "options", "correct"]):
        return jsonify({"message": "Missing required fields"}), 400

    # Ensure 'options' is a list
    if not isinstance(data["options"], list) or len(data["options"]) != 4:
        return jsonify({"message": "Options should be a list of exactly 4 items"}), 400

    # Get next unique question ID
    new_id = get_next_question_id()

    question_data = {
        "id": new_id,
        "question": data["question"],
        "options": data["options"],
        "correct": data["correct"]
    }

    # Insert question into MongoDB
    questions_collection.insert_one(question_data)

    return jsonify({"message": "Question added successfully", "id": new_id}), 201

# ------------------ Get Questions API ------------------
@app.route("/get-questions", methods=["GET"])
def get_questions():
    questions = list(questions_collection.find({}, {"_id": 0}))  # Exclude MongoDB _id field
    return jsonify(questions)


# ------------------ User Registration (Updated) ------------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json

    # Extract form data
    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("email")
    password = data.get("password")
    guardian_name = data.get("guardianName")
    guardian_contact = data.get("guardianContact")
    address = data.get("address")
    city = data.get("city")
    state = data.get("state")
    country = data.get("country")
    pin_code = data.get("pinCode")

    # Validate required fields
    if not (
            first_name and last_name and email and password and guardian_name and guardian_contact and address and city and state and country and pin_code):
        return jsonify({"message": "All fields are required"}), 400

    # Check if the email is already registered
    if users_collection.find_one({"email": email}):
        return jsonify({"message": "User already exists"}), 400

    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Store user in database
    user_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_password,
        "guardian_name": guardian_name,
        "guardian_contact": guardian_contact,
        "address": {
            "street": address,
            "city": city,
            "state": state,
            "country": country,
            "pin_code": pin_code
        }
    }

    users_collection.insert_one(user_data)

    return jsonify({"message": "User registered successfully"}), 201


# ------------------ User Login ------------------
@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = users_collection.find_one({"email": email})
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=email, expires_delta=datetime.timedelta(hours=1))
    return jsonify({"message": "Login successful", "token": access_token, "username": user["first_name"]}), 200


# ------------------ Protected Route (Dashboard) ------------------
@app.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Welcome {current_user} to the dashboard!"})


# ------------------ Forgot Password (Send Reset Link) ------------------
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    user = users_collection.find_one({"email": email})
    if not user:
        return jsonify({"message": "User not found"}), 404

    reset_token = secrets.token_hex(16)
    users_collection.update_one({"email": email}, {"$set": {"reset_token": reset_token}})

    reset_link = f"http://localhost:3000/reset-password?token={reset_token}&email={email}"

    # Send Email
    msg = Message("Password Reset Request", recipients=[email])
    msg.body = f"Click the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, ignore this email."

    try:
        mail.send(msg)
        return jsonify({"message": "Reset link sent to email"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to send email", "error": str(e)}), 500


# ------------------ Reset Password ------------------
@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    email = data.get("email")
    new_password = data.get("new_password")
    reset_token = data.get("token")

    user = users_collection.find_one({"email": email, "reset_token": reset_token})
    if not user:
        return jsonify({"message": "Invalid reset token"}), 400

    hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

    users_collection.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}, "$unset": {"reset_token": ""}}
    )

    return jsonify({"message": "Password reset successfully"}), 200


if __name__ == "__main__":
    app.run(debug=True)
