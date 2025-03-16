from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import secrets
from flask_cors import CORS

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/mydatabase"
app.config["JWT_SECRET_KEY"] = "supersecretkey"
CORS(app)

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)




@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"message": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    mongo.db.users.insert_one({"email": email, "password": hashed_password})

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/signin", methods=["POST"])
def signin():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = mongo.db.users.find_one({"email": email})
    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"message": "Invalid email or password"}), 401

    access_token = create_access_token(identity=email)
    return jsonify({"message": "Login successful", "token": access_token}), 200


@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"message": "Email is required"}), 400

    user = mongo.db.users.find_one({"email": email})

    if not user:
        return jsonify({"message": "Email not found"}), 404

    # Generate a secure reset token
    reset_token = secrets.token_hex(16)

    # Store the token in the database
    mongo.db.users.update_one({"email": email}, {"$set": {"reset_token": reset_token}})

    return jsonify({"message": "Password reset token generated", "reset_token": reset_token}), 200


@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    email = data.get("email")
    reset_token = data.get("reset_token")
    new_password = data.get("new_password")

    if not email or not reset_token or not new_password:
        return jsonify({"message": "All fields are required"}), 400

    user = mongo.db.users.find_one({"email": email})

    if not user:
        return jsonify({"message": "Email not found"}), 404

    if "reset_token" not in user or user["reset_token"] != reset_token:
        return jsonify({"message": "Invalid or expired reset token"}), 400

    # Validate new password
    new_password = new_password.strip()
    if not new_password:
        return jsonify({"message": "Password cannot be empty"}), 400

    hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")

    mongo.db.users.update_one(
        {"email": email},
        {"$set": {"password": hashed_password}, "$unset": {"reset_token": ""}}
    )

    return jsonify({"message": "Password reset successfully"}), 200


if __name__ == "__main__":
    app.run(debug=True)
