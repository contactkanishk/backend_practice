from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from flask_mail import Message
import datetime
import secrets
from db import users_collection
from extensions import bcrypt, mail  # Import from extensions.py

auth_bp = Blueprint("auth", __name__)



# ------------------ User Signup ------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json
    required_fields = ["firstName", "lastName", "email", "password", "guardianName", "guardianContact", "address", "city", "state", "country", "pinCode"]

    if not all(field in data for field in required_fields):
        return jsonify({"message": "All fields are required"}), 400

    if users_collection.find_one({"email": data["email"]}):
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    user_data = {
        "first_name": data["firstName"],
        "last_name": data["lastName"],
        "email": data["email"],
        "password": hashed_password,
        "guardian_name": data["guardianName"],
        "guardian_contact": data["guardianContact"],
        "address": {
            "street": data["address"],
            "city": data["city"],
            "state": data["state"],
            "country": data["country"],
            "pin_code": data["pinCode"]
        }
    }

    users_collection.insert_one(user_data)
    return jsonify({"message": "User registered successfully"}), 201

# ------------------ User Login ------------------
@auth_bp.route("/signin", methods=["POST"])
def signin():
    data = request.json
    user = users_collection.find_one({"email": data["email"]})

    if not user or not bcrypt.check_password_hash(user["password"], data["password"]):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=data["email"], expires_delta=datetime.timedelta(hours=1))
    return jsonify({"message": "Login successful", "token": access_token, "username": user["first_name"]}), 200

# ------------------ Forgot Password ------------------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    user = users_collection.find_one({"email": data["email"]})

    if not user:
        return jsonify({"message": "User not found"}), 404

    reset_token = secrets.token_hex(16)
    users_collection.update_one({"email": data["email"]}, {"$set": {"reset_token": reset_token}})

    reset_link = f"http://localhost:3000/reset-password?token={reset_token}&email={data['email']}"

    msg = Message("Password Reset Request", recipients=[data["email"]])
    msg.body = f"Click to reset your password: {reset_link}"

    try:
        mail.send(msg)
        return jsonify({"message": "Reset link sent to email"}), 200
    except Exception as e:
        return jsonify({"message": "Failed to send email", "error": str(e)}), 500

# ------------------ Reset Password ------------------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    user = users_collection.find_one({"email": data["email"], "reset_token": data["token"]})

    if not user:
        return jsonify({"message": "Invalid reset token"}), 400

    hashed_password = bcrypt.generate_password_hash(data["new_password"]).decode("utf-8")

    users_collection.update_one(
        {"email": data["email"]},
        {"$set": {"password": hashed_password}, "$unset": {"reset_token": ""}}
    )

    return jsonify({"message": "Password reset successfully"}), 200
