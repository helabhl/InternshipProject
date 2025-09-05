from flask import Blueprint, request, jsonify
from controllers.quizController import (
    create_quiz,
    get_all_quizzes,
    get_quiz_by_id,
    update_quiz,
    delete_quiz,
    get_quizzes_by_subject,
    get_all_subjects
)

quiz_bp = Blueprint("quizesdata", __name__, url_prefix="/quiz")


@quiz_bp.route("/", methods=["POST"])
def create_quiz_route():
    data = request.get_json()
    response, status = create_quiz(data)
    return jsonify(response), status


@quiz_bp.route("/", methods=["GET"])
def get_all_quizzes_route():
    response, status = get_all_quizzes()
    return jsonify(response), status


@quiz_bp.route("/<quiz_id>", methods=["GET"])
def get_quiz_by_id_route(quiz_id):
    response, status = get_quiz_by_id(quiz_id)
    return jsonify(response), status


@quiz_bp.route("/<quiz_id>", methods=["PUT"])
def update_quiz_route(quiz_id):
    data = request.get_json()
    response, status = update_quiz(quiz_id, data)
    return jsonify(response), status


@quiz_bp.route("/<quiz_id>", methods=["DELETE"])
def delete_quiz_route(quiz_id):
    response, status = delete_quiz(quiz_id)
    return jsonify(response), status


@quiz_bp.route("/subject/<subject_name>", methods=["GET"])
def get_quizzes_by_subject_route(subject_name):
    response, status = get_quizzes_by_subject(subject_name)
    return jsonify(response), status


@quiz_bp.route("/subjects", methods=["GET"])
def get_all_subjects_route():
    response, status = get_all_subjects()
    return jsonify(response), status
