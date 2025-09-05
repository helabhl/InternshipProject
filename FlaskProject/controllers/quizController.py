from models.quiz import Quiz
from bson import ObjectId
from bson.errors import InvalidId


def mongo_to_dict(obj):
    """Convertit un document MongoEngine en dict avec _id en string."""
    data = obj.to_mongo().to_dict()
    data["_id"] = str(data["_id"])
    return data


def create_quiz(data):
    try:
        quiz = Quiz(**data)
        quiz.save()
        return {"message": "Quiz created", "id": str(quiz.id)}, 201
    except Exception as e:
        return {"error": str(e)}, 400


def get_all_quizzes():
    quizzes = Quiz.objects()
    return [mongo_to_dict(q) for q in quizzes], 200


def get_quiz_by_id(quiz_id):
    try:
        ObjectId(quiz_id)  # validation
    except InvalidId:
        return {"error": "Invalid quiz ID"}, 400

    quiz = Quiz.objects(id=quiz_id).first()
    if not quiz:
        return {"error": "Quiz not found"}, 404
    return mongo_to_dict(quiz), 200


def update_quiz(quiz_id, data):
    try:
        ObjectId(quiz_id)
    except InvalidId:
        return {"error": "Invalid quiz ID"}, 400

    quiz = Quiz.objects(id=quiz_id).first()
    if not quiz:
        return {"error": "Quiz not found"}, 404

    try:
        quiz.update(**data)
        return {"message": "Quiz updated"}, 200
    except Exception as e:
        return {"error": str(e)}, 400


def delete_quiz(quiz_id):
    try:
        ObjectId(quiz_id)
    except InvalidId:
        return {"error": "Invalid quiz ID"}, 400

    quiz = Quiz.objects(id=quiz_id).first()
    if not quiz:
        return {"error": "Quiz not found"}, 404

    quiz.delete()
    return {"message": "Quiz deleted"}, 200


def get_quizzes_by_subject(subject_name):
    quizzes = Quiz.objects(subject=subject_name)
    if not quizzes:
        return {"message": f"No quizzes found for subject '{subject_name}'"}, 404
    return [mongo_to_dict(q) for q in quizzes], 200


def get_all_subjects():
    subjects = Quiz.objects().distinct('subject')
    if not subjects:
        return {"message": "No subjects found"}, 404
    return {"subjects": subjects}, 200
