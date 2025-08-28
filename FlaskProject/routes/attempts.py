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

def calculate_score(answers, time_spent):
    num_questions = len(answers)
    if num_questions == 0:
        return 0.0

    sum_success_rate = 0
    for ans in answers:
        numerator = ans.correct_answer
        denominator = ans.wrong_answer + ans.hint_used + 1  # éviter /0
        sum_success_rate += numerator / denominator

    avg_success_rate = sum_success_rate / num_questions

    correct_count = sum(a.correct_answer for a in answers)
    time_per_question = time_spent / correct_count if correct_count > 0 else 0

    min_time = 120
    max_time = 300
    if time_per_question < min_time:
        speed = 1
    elif time_per_question <= max_time:
        speed = 1 - (time_per_question - min_time) / (max_time - min_time)
    else:
        speed = 0

    return 0.9 * avg_success_rate + 0.1 * speed

@attempts_bp.route('/attempts', methods=['POST'])
def create_or_update_attempt():
    try:
        data = request.get_json()

        userID = data.get("userID")
        kidIndex = data.get("kidIndex")
        quizID = data.get("quizID")
        question_index = data.get("question_index")
        is_correct = int(data.get("is_correct", 0))
        hint_used = int(data.get("hint_used", 0))
        is_wrong = int(data.get("is_wrong", 0))

        if not all([userID, kidIndex, quizID]) or question_index is None:
            return jsonify({"error": "Champs manquants"}), 400

        if not ObjectId.is_valid(quizID):
            return jsonify({"error": "quizID invalide"}), 400

        quizID = ObjectId(quizID)
        quiz = Quiz.objects(id=quizID).first()
        if not quiz:
            return jsonify({"error": "Quiz non trouvé"}), 404

        num_questions = len(quiz.questions)

        # Récupération ou création
        attempt = AttemptData.objects(
            userID=userID,
            kidIndex=kidIndex,
            quizID=quizID,
            completed=0,
            failed=0,
            abandoned=0
        ).first()

        created = False
        if not attempt:
            created = True
            now = datetime.now(timezone.utc)  # UTC aware
            attempt = AttemptData(
                userID=userID,
                kidIndex=kidIndex,
                quizID=quizID,
                start_time=now
            )
            attempt.init_answers(num_questions)

        # Met à jour la question spécifique
        attempt.answers[question_index].correct_answer = is_correct
        attempt.answers[question_index].hint_used += hint_used
        attempt.answers[question_index].wrong_answer += is_wrong

        # Met à jour les temps
        attempt.end_time = datetime.now(timezone.utc)  # UTC aware

        # Calcul du score
        correct_answers = sum(q.correct_answer for q in attempt.answers)
        total_wrong_attempts = sum(q.wrong_answer for q in attempt.answers)

        if correct_answers == num_questions:
            attempt.completed = 1
        elif total_wrong_attempts >= 3:
            attempt.failed = 1


        now = datetime.utcnow()  # naive UTC
        time_spent = int((now - attempt.start_time).total_seconds())
        attempt.score = calculate_score(attempt.answers, time_spent)

        attempt.save()

        status = "completed" if attempt.completed else \
                 "failed" if attempt.failed else \
                 "abandoned" if attempt.abandoned else \
                 "in_progress"

        return jsonify({
            "message": "Tentative créée" if created else "Tentative mise à jour",
            "score": attempt.score,
            "status": status,
            "attempt_id": str(attempt.id)
        }), 200

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
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

