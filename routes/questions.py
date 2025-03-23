from flask import Blueprint, request, jsonify
from db import questions_collection, counters_collection

questions_bp = Blueprint("questions", __name__)

def get_next_question_id():
    counter = counters_collection.find_one_and_update(
        {"_id": "question_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return counter["sequence_value"]

@questions_bp.route("/add-question", methods=["POST"])
def add_question():
    data = request.json

    if not all(key in data for key in ["question", "options", "correct"]):
        return jsonify({"message": "Missing required fields"}), 400

    if not isinstance(data["options"], list) or len(data["options"]) != 4:
        return jsonify({"message": "Options should be a list of exactly 4 items"}), 400

    # Check if question already exists
    existing_question = questions_collection.find_one({"question": data["question"]})
    if existing_question:
        return jsonify({"message": "Question already exists"}), 400

    new_id = get_next_question_id()

    question_data = {
        "id": new_id,
        "question": data["question"],
        "options": data["options"],
        "correct": data["correct"]
    }

    questions_collection.insert_one(question_data)
    return jsonify({"message": "Question added successfully", "id": new_id}), 201

@questions_bp.route("/get-questions", methods=["GET"])
def get_questions():
    questions = list(questions_collection.find({}, {"_id": 0}))
    return jsonify(questions)
