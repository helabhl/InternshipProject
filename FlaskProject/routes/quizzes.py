from flask import Blueprint, request, jsonify
from models.quiz import Quiz

quiz_bp = Blueprint("quizesdata", __name__, url_prefix="/quiz")


@quiz_bp.route('/', methods=['POST'])
def create_quiz():
    data = request.get_json()
    # Vérification de doublon
    if Quiz.objects(key=data.get('key')).first():
        return jsonify({"error": "Quiz with this key already exists"}), 400
    try:
        quiz = Quiz(**data)
        quiz.save()
        return jsonify({"message": "Quiz created", "id": str(quiz.id)}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


from bson import ObjectId

def mongo_to_dict(obj):
    """Convertit un document MongoEngine en dict avec _id en string."""
    data = obj.to_mongo().to_dict()
    data["_id"] = str(data["_id"])
    return data

@quiz_bp.route('/', methods=['GET'])
def get_all_quizzes():
    quizzes = Quiz.objects()
    return jsonify([mongo_to_dict(q) for q in quizzes]), 200

from bson.errors import InvalidId

@quiz_bp.route('/<quiz_id>', methods=['GET'])
def get_quiz_by_id(quiz_id):
    try:
        # Validation de l'ObjectId
        oid = ObjectId(quiz_id)
    except InvalidId:
        return jsonify({"error": "Invalid quiz ID"}), 400
    
    quiz = Quiz.objects(id=quiz_id).first()
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    return jsonify(mongo_to_dict(quiz)), 200


@quiz_bp.route('/<quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    try:
        # Validation de l'ObjectId
        oid = ObjectId(quiz_id)
    except InvalidId:
        return jsonify({"error": "Invalid quiz ID"}), 400
    data = request.get_json()
    quiz = Quiz.objects(id=quiz_id).first()
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    try:
        quiz.update(**data)
        return jsonify({"message": "Quiz updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@quiz_bp.route('/<quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    try:
        # Validation de l'ObjectId
        oid = ObjectId(quiz_id)
    except InvalidId:
        return jsonify({"error": "Invalid quiz ID"}), 400
    quiz = Quiz.objects(id=quiz_id).first()
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404
    quiz.delete()
    return jsonify({"message": "Quiz deleted"}), 200


@quiz_bp.route('/subject/<subject_name>', methods=['GET'])
def get_quizzes_by_subject(subject_name):
    quizzes = Quiz.objects(subject=subject_name)
    if not quizzes:
        return jsonify({"message": f"No quizzes found for subject '{subject_name}'"}), 404
    return jsonify([mongo_to_dict(q) for q in quizzes]), 200


@quiz_bp.route('/subjects', methods=['GET'])
def get_all_subjects():
    # Récupérer uniquement le champ subject de tous les quizzes
    subjects = Quiz.objects().distinct('subject')

    if not subjects:
        return jsonify({"message": "No subjects found"}), 404
    
    return jsonify({"subjects": subjects}), 200
