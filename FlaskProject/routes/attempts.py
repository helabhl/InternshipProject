# routes/quiz_attempts.py
from flask import Blueprint, request, jsonify
from models.attempt import AttemptData
from models.quiz import Quiz
from bson import ObjectId
from mongoengine.errors import ValidationError
from datetime import datetime, timedelta, timezone
import pandas as pd
from typing import Dict, List, Tuple, Any


attempts_bp = Blueprint("attemptsdata", __name__)

def mongo_to_dict(obj):
    data = obj.to_mongo().to_dict()
    data["_id"] = str(data["_id"])
    if "quizID" in data:
        data["quizID"] = str(data["quizID"])
    return data

def calculate_score(answers, min_time=120, max_time=300):
    num_questions = len(answers)
    if num_questions == 0:
        return 0.0

    sum_success_rate = 0
    for ans in answers:
        # Calcul du speed selon le temps par question
        if ans.time_per_question < min_time:
            speed = 1
        elif ans.time_per_question <= max_time:
            speed = 1 - (ans.time_per_question - min_time) / (max_time - min_time)
        else:
            speed = 0

        # Calcul du success rate pondéré
        numerator = ans.correct_answer
        denominator = ans.wrong_answer + ans.hint_used + 1  # éviter /0
        sum_success_rate += 0.9 * (numerator / denominator) + 0.1 * speed

    avg_success_rate = sum_success_rate / num_questions
    return avg_success_rate

@attempts_bp.route('/attempts', methods=['POST'])
def create_attempt():
    try:
        data = request.get_json()
        userID = data.get("userID")
        kidIndex = data.get("kidIndex")
        quizID = data.get("quizID")
        deviceType = data.get("device")   


        if not all([userID, kidIndex, quizID]):
            return jsonify({"error": "Champs manquants"}), 400
        if not ObjectId.is_valid(quizID):
            return jsonify({"error": "quizID invalide"}), 400

        quizID = ObjectId(quizID)
        quiz = Quiz.objects(id=quizID).first()
        if not quiz:
            return jsonify({"error": "Quiz non trouvé"}), 404

        num_questions = len(quiz.questions)

        # Vérifier qu'il n'existe pas déjà une tentative active
        attempt = AttemptData.objects(
            userID=userID,
            kidIndex=kidIndex,
            quizID=quizID,
            deviceType=deviceType,
            completed=0,
            failed=0,
            abandoned=0
        ).first()
        if attempt:
            return jsonify({"error": "Une tentative est déjà en cours"}), 400

        # Création de la tentative
        attempt = AttemptData(
            userID=userID,
            kidIndex=kidIndex,
            quizID=quizID,
            deviceType=device,
        )
        attempt.init_answers(num_questions)
        attempt.save()

        return jsonify({
            "message": "Tentative créée",
            "attempt_id": str(attempt.id)
        }), 201

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@attempts_bp.route('/attempts/<attempt_id>', methods=['PUT'])
def update_attempt(attempt_id):
    try:
        if not ObjectId.is_valid(attempt_id):
            return jsonify({"error": "attempt_id invalide"}), 400

        attempt = AttemptData.objects(id=ObjectId(attempt_id)).first()
        if not attempt:
            return jsonify({"error": "Tentative non trouvée"}), 404

        data = request.get_json()
        question_index = data.get("question_index")
        is_correct = int(data.get("is_correct", 0))
        hint_used = int(data.get("hint_used", 0))
        is_wrong = int(data.get("is_wrong", 0))
        start_time_str = data.get("start_time")

        num_questions = len(attempt.answers)

        # Vérifier l'index
        if question_index is None or question_index < 0 or question_index >= num_questions:
            return jsonify({"error": f"L'index de question {question_index} est invalide. Valeurs valides : 0 à {num_questions - 1}"}), 400

        # Vérifier progression séquentielle
        if question_index > 0 and attempt.answers[question_index - 1].correct_answer == 0:
            return jsonify({"error": f"Vous devez d'abord répondre correctement à la question {question_index - 1}"}), 400

        # Vérifier verrouillage de la question
        if attempt.answers[question_index].correct_answer == 1:
            return jsonify({"error": f"La question {question_index} est déjà correcte, vous ne pouvez plus la modifier"}), 400

        # Vérifier start_time
        if not start_time_str:
            return jsonify({"error": "start_time de la question manquant"}), 400
        question_start_time = datetime.fromisoformat(start_time_str)
        attempt.answers[question_index].start_time = question_start_time

        # end_time = maintenant (UTC aware)
        now = datetime.now(timezone.utc)
        attempt.answers[question_index].end_time = now

        # temps écoulé
        attempt.answers[question_index].time_per_question = int(
            (attempt.answers[question_index].end_time - attempt.answers[question_index].start_time).total_seconds()
        )

        # Mettre à jour les statistiques
        attempt.answers[question_index].correct_answer = is_correct
        attempt.answers[question_index].hint_used += hint_used
        attempt.answers[question_index].wrong_answer += is_wrong

        correct_answers = sum(q.correct_answer for q in attempt.answers)
        total_wrong_attempts = sum(q.wrong_answer for q in attempt.answers)

        if correct_answers == num_questions:
            attempt.completed = 1
        elif total_wrong_attempts >= 3:
            attempt.failed = 1

        total_time = sum(a.time_per_question for a in attempt.answers)
        attempt.score = calculate_score(attempt.answers, total_time)

        attempt.save()

        status = "completed" if attempt.completed else \
                 "failed" if attempt.failed else \
                 "abandoned" if attempt.abandoned else \
                 "in_progress"

        return jsonify({
            "message": "Réponse mise à jour",
            "score": attempt.score,
            "status": status,
            "attempt_id": str(attempt.id)
        }), 200

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@attempts_bp.route('/attempts/recalculate_scores', methods=['POST'])
def recalculate_scores():
    """
    Recalcule le score de toutes les tentatives existantes
    """
    try:
        attempts = AttemptData.objects()  # Récupère toutes les tentatives
        for attempt in attempts:
            # Recalculer le score avec la nouvelle fonction
            attempt.score = calculate_score(attempt.answers)
            attempt.save()

        return jsonify({
            "message": f"Scores recalculés pour toutes les tentatives"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@attempts_bp.route('/attempts/<attempt_id>/abandon', methods=['POST'])
def abandon_attempt(attempt_id):
    attempt = AttemptData.objects(id=attempt_id).first()
    if not attempt:
        return jsonify({"error": "Attempt non trouvé"}), 404

    if attempt.completed or attempt.failed or attempt.abandoned:
        return jsonify({"message": "Attempt déjà terminé"}), 400

    attempt.abandoned = 1
    attempt.end_time = datetime.now(timezone.utc)  # UTC aware
    attempt.time_spent = int((attempt.end_time - attempt.start_time).total_seconds())
    attempt.save()

    return jsonify({"message": "Quiz abandonné"}), 200

def mark_abandoned_attempts():
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)  # UTC aware
    attempts = AttemptData.objects(
        completed=0,
        failed=0,
        abandoned=0,
        start_time__lt=one_hour_ago
    )

    for attempt in attempts:
        attempt.abandoned = 1
        attempt.end_time = attempt.start_time + timedelta(hours=1)
        attempt.time_spent = 3600
        attempt.save()

# Get all
@attempts_bp.route('/attempts', methods=['GET'])
def get_all_attempts():
    attempts = AttemptData.objects()
    return jsonify([mongo_to_dict(a) for a in attempts]), 200

# Get by ID
@attempts_bp.route('/attempts/<attempt_id>', methods=['GET'])
def get_attempt_by_id(attempt_id):
    try:
        attempt = AttemptData.objects(id=ObjectId(attempt_id)).first()
        if not attempt:
            return jsonify({"error": "Attempt not found"}), 404
        return jsonify(mongo_to_dict(attempt)), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@attempts_bp.route('/attempts/<user_id>/<kid_index>', methods=['GET'])
def get_attempts_per_kid(user_id, kid_index):
    try:
        parent = AttemptData.objects(userID=user_id, kidIndex=kid_index)
        if not parent:
            return jsonify({"error": "Parent not found"}), 404

        from_str = request.args.get("from")
        to_str = request.args.get("to")
        to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
        from_date = to_date - timedelta(days=7) if not from_str else datetime.fromisoformat(from_str)

        attempts = AttemptData.objects(
            userID=user_id,
            kidIndex=kid_index,
            start_time__gte=from_date,
            start_time__lte=to_date
        )

        results = []
        for a in attempts:
            quiz = Quiz.objects(id=a.quizID).first()
            results.append({
                "id": str(a.id),
                "quizID": str(a.quizID),
                "level": quiz.level,
                "subject": quiz.subject,
                "start_time": a.start_time,
                "end_time": a.end_time,
                "score": a.score,
                "completed": a.completed,
                "failed": a.failed,
                "abandoned": a.abandoned
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@attempts_bp.route('/attempts/<user_id>/<kid_index>/week/<week_str>', methods=['GET'])
def get_attempts_per_week(user_id, kid_index, week_str):
    try:
        parent = AttemptData.objects(userID=user_id, kidIndex=kid_index)
        if not parent:
            return jsonify({"error": "Parent not found"}), 404

        year, week_num = map(int, week_str.split("-W"))

        start_date = datetime.fromisocalendar(year, week_num, 1).replace(tzinfo=timezone.utc)
        end_date = (datetime.fromisocalendar(year, week_num, 7) + timedelta(days=1)).replace(tzinfo=timezone.utc)

        attempts = AttemptData.objects(
            userID=user_id,
            kidIndex=kid_index,
            start_time__gte=start_date,
            start_time__lt=end_date
        )

        results = []
        for a in attempts:
            quiz = Quiz.objects(id=a.quizID).first()
            results.append({
                "id": str(a.id),
                "quizID": str(a.quizID),
                "level": quiz.level,
                "subject": quiz.subject,
                "chapter": quiz.chapter,
                "start_time": a.start_time,
                "end_time": a.end_time,
                "score": a.score,
                "completed": a.completed,
                "failed": a.failed,
                "abandoned": a.abandoned
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@attempts_bp.route('/attempts/<user_id>/<kid_index>/month/<month_str>', methods=['GET'])
def get_attempts_per_month(user_id, kid_index, month_str):
    try:
        parent = AttemptData.objects(userID=user_id, kidIndex=kid_index)
        if not parent:
            return jsonify({"error": "Parent not found"}), 404

        year, month = map(int, month_str.split("-"))
        if not (1 <= month <= 12):
            raise ValueError

        start_date = datetime(year, month, 1, tzinfo=timezone.utc)
        if month == 12:
            end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

        attempts = AttemptData.objects(
            userID=user_id,
            kidIndex=kid_index,
            start_time__gte=start_date,
            start_time__lt=end_date
        )

        results = []
        for a in attempts:
            quiz = Quiz.objects(id=a.quizID).first()
            results.append({
                "id": str(a.id),
                "quizID": str(a.quizID),
                "level": quiz.level,
                "subject": quiz.subject,
                "chapter": quiz.chapter,
                "start_time": a.start_time,
                "end_time": a.end_time,
                "score": a.score,
                "completed": a.completed,
                "failed": a.failed,
                "abandoned": a.abandoned
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

