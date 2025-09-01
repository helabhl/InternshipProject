# routes/quiz_attempts.py
from flask import Blueprint, request, jsonify
from models.attempt import AttemptData, QuestionAttempt
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

def calculate_score(answers, min_time=60, max_time=300):
    num_questions = len(answers)
    if num_questions == 0:
        return 0.0

    sum_success_rate = 0
    for ans in answers:
        t = ans.time_per_question or 0  # éviter None

        # Calcul du speed (borné entre 0 et 1)
        if t < min_time:
            speed = 1
        elif t <= max_time:
            speed = 1 - (t - min_time) / (max_time - min_time)
        else:
            speed = 0
        speed = max(0, min(1, speed))  # clamp entre 0 et 1

        # Calcul du success rate pondéré
        numerator = ans.correct_answer
        denominator = ans.wrong_answer + ans.hint_used + 1  # éviter /0
        success = numerator / denominator

        sum_success_rate += 0.8*success+0.2*ans.correct_answer*speed

    avg_success_rate = sum_success_rate /num_questions
    return avg_success_rate

@attempts_bp.route('/create-attempt', methods=['POST'])
def create_attempt():
    try:
        data = request.get_json()
        userID = data.get("userID")
        kidIndex = data.get("kidIndex")
        quizID = data.get("quizID")
        deviceType = data.get("deviceType")   
        device = data.get("device")   


        if not all([userID, kidIndex, quizID]):
            return jsonify({"error": "Champs manquants"}), 400
        if not ObjectId.is_valid(quizID):
            return jsonify({"error": "quizID invalide"}), 400

        quizID = ObjectId(quizID)
        quiz = Quiz.objects(id=quizID).first()
        if not quiz:
            return jsonify({"error": "Quiz non trouvé"}), 404

        num_questions = len(quiz.questions)

        stats = AttemptData.objects(userID=userID, kidIndex=kidIndex, quizID=quizID).first()
        if not stats:
            stats = AttemptData(userID=userID, kidIndex=kidIndex, quizID=quizID, total_attempts=0)

        # Incrémenter le compteur global
        stats.total_attempts += 1

        # Création de la tentative
        attempt = AttemptData(
            userID=userID,
            kidIndex=kidIndex,
            quizID=quizID,
            deviceType=deviceType,
            device=device,
            total_attempts=stats.total_attempts
        )
        attempt.init_answers(num_questions)
        now = datetime.now(timezone.utc)
        attempt.start_time = now


        

        attempt.save()

        return jsonify({
            "message": "Tentative créée",
            "attempt_id": str(attempt.id)
        }), 201

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@attempts_bp.route('/update-attempt', methods=['POST'])
def update_attempt():
    try:
        def to_utc_aware(dt):
            """Convertir datetime naïf en UTC aware"""
            if dt and dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        data = request.get_json()
        attempt_id = data.get("attempt_id")
        question_index = data.get("question_index")
        is_correct = int(data.get("is_correct", 0))
        hint_used = int(data.get("hint_used", 0))
        is_wrong = int(data.get("is_wrong", 0))
        is_starting = bool(data.get("is_starting", False))
        response_value = data.get("response_value", "")

        # Vérif id valide
        if not ObjectId.is_valid(attempt_id):
            return jsonify({"error": "attempt_id invalide"}), 400

        attempt = AttemptData.objects(id=ObjectId(attempt_id)).first()
        if not attempt:
            return jsonify({"error": "Tentative non trouvée"}), 404

        num_questions = len(attempt.answers)

        # Vérifier l'index
        if question_index is None or question_index < 0 or question_index >= num_questions:
            return jsonify({"error": f"L'index de question {question_index} est invalide. Valeurs valides : 0 à {num_questions - 1}"}), 400

        # Vérifier progression séquentielle
        if question_index > 0 and attempt.answers[question_index - 1].correct_answer == 0:
            return jsonify({"error": f"Vous devez d'abord répondre correctement à la question {question_index - 1}"}), 400

        # Vérifier verrouillage
        if attempt.answers[question_index].correct_answer == 1:
            return jsonify({"error": f"La question {question_index} est déjà correcte, vous ne pouvez plus la modifier"}), 400

        now = datetime.now(timezone.utc)
        answer = attempt.answers[question_index]

        if is_starting:
            # ➕ Créer un nouvel objet tentative (vide, juste ouvert)
            qa = QuestionAttempt(
                is_correct=0,
                is_wrong=0,
                hint_used=0,
                start_time=now,
                response_value=""
            )
            answer.start_time = now  # global start pour la question
            answer.attempts.append(qa)

        else:
            # Finir la tentative en cours → la dernière tentative ouverte
            if not answer.attempts or not answer.attempts[-1].start_time:
                return jsonify({"error": "Aucune tentative en cours pour cette question"}), 400

            qa = answer.attempts[-1]
            qa.end_time = now
            qa.is_correct = is_correct
            qa.is_wrong = is_wrong
            qa.hint_used = hint_used
            qa.response_value = response_value
            qa.duration = int((to_utc_aware(now) - to_utc_aware(qa.start_time)).total_seconds())

            # Mise à jour des agrégats Answer
            answer.end_time = now
            answer.attempts_count = len(answer.attempts)
            answer.correct_answer = sum(a.is_correct for a in answer.attempts)
            answer.wrong_answer = sum(a.is_wrong for a in answer.attempts)
            answer.hint_used = sum(a.hint_used for a in answer.attempts)
            answer.time_per_question = sum(a.duration for a in answer.attempts)

        # 🔄 Stats globales
        correct_answers = sum(answer.correct_answer for answer in attempt.answers)
        total_wrong_attempts = sum(answer.wrong_answer for answer in attempt.answers)

        if correct_answers == num_questions:
            attempt.completed = 1
            attempt.end_time = now
        elif total_wrong_attempts >= 3:
            attempt.failed = 1
            attempt.end_time = now


        # Durée totale du quiz
        if attempt.start_time and attempt.end_time:
            attempt.duration = int((to_utc_aware(attempt.end_time) - to_utc_aware(attempt.start_time)).total_seconds())
        attempt.updated_at = now

        attempt.score = calculate_score(attempt.answers, 60, 300)

        attempt.save()

        status = "completed" if attempt.completed else \
                 "failed" if attempt.failed else \
                 "aborted" if getattr(attempt, "aborted", 0) else \
                 "in_progress"

        response = {
            "message": "Réponse mise à jour",
            "status": status,
            "attempt_id": str(attempt.id)
        }
        if not is_starting:
            response["score"] = attempt.score

        return jsonify(response), 200

    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@attempts_bp.route('/attempts/abandon', methods=['POST'])
def abandon_attempt():
    data = request.get_json()

    attempt_id = data.get("attempt_id")

    if not attempt_id or not ObjectId.is_valid(attempt_id):
        return jsonify({"error": "attempt_id invalide"}), 400

    attempt = AttemptData.objects(id=ObjectId(attempt_id)).first()
    if not attempt:
        return jsonify({"error": "Attempt non trouvé"}), 404

    if attempt.completed or attempt.failed or attempt.aborted or attempt.timeout:
        return jsonify({"message": "Attempt déjà terminé"}), 400

    # Marquer comàme abandonné
    attempt.aborted = 1
    attempt.end_time = datetime.now(timezone.utc)


    attempt.save()

    return jsonify({
        "message": "Quiz abandonné",
        "attempt_id": str(attempt.id)
    }), 200

def mark_timeout_attempts():
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)  # UTC aware
    attempts = AttemptData.objects(
        completed=0,
        failed=0,
        aborted=0,
        timeout = 0,
        start_time__lt=one_hour_ago
    )

    for attempt in attempts:
        attempt.timeout = 1
        attempt.end_time = attempt.start_time + timedelta(hours=1)
        attempt.time_spent = 3600
        attempt.save()


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
                "aborted": a.aborted
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
                "aborted": a.aborted
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
                "aborted": a.aborted
            })

        return jsonify(results), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
