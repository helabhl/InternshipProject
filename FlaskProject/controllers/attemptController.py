from models.attempt import AttemptData, QuestionAttempt
from models.quiz import Quiz
from bson import ObjectId
from bson.errors import InvalidId
from mongoengine.errors import ValidationError
from datetime import datetime, timedelta, timezone
from math import log

def mongo_to_dict(obj):
    data = obj.to_mongo().to_dict()
    data["_id"] = str(data["_id"])
    if "quizID" in data:
        data["quizID"] = str(data["quizID"])
    return data


def calculate_score(answers, attempts_count, min_time=0, max_time=90):
    num_questions = len(answers)
    if num_questions == 0:
        return 0.0, 0.0

    sum_success_rate = 0
    sum_speed = 0
    for ans in answers:
        t = ans.duration or 0
        # Calculate speed
        if t < min_time:
            speed = 1
        elif t <= max_time:
            speed = 1 - (t - min_time) / (max_time - min_time)
        else:
            speed = 0
        speed = max(0, min(1, speed))

        numerator = ans.correct_answer
        denominator = ans.wrong_answer + ans.hint_used + 1
        success = numerator / denominator

        sum_success_rate += success
        sum_speed += ans.correct_answer * speed

    avg_success_rate = sum_success_rate / num_questions
    avg_speed = sum_speed / num_questions

    score = (
        0.7 * avg_success_rate
        + 0.2 * avg_speed
        + 0.1 * (1 / (1 + log(attempts_count)))
    )
    return score, avg_success_rate


# ------------------ CRUD & LOGIC -------------------

def create_attempt(data):
    try:
        userID = data.get("userID")
        kidIndex = data.get("kidIndex")
        quizID = data.get("quizID")
        deviceType = data.get("deviceType")
        device = data.get("device")

        if not all([userID, kidIndex, quizID]):
            return {"error": "Missing fields"}, 400
        if not ObjectId.is_valid(quizID):
            return {"error": "Invalid quizID"}, 400

        quizID = ObjectId(quizID)
        quiz = Quiz.objects(id=quizID).first()
        if not quiz:
            return {"error": "Quiz not found"}, 404

        num_questions = len(quiz.questions)

        stats = AttemptData.objects(userID=userID, kidIndex=kidIndex, quizID=quizID).first()
        if not stats:
            stats = AttemptData(userID=userID, kidIndex=kidIndex, quizID=quizID, attempts_count=0)

        stats.attempts_count += 1
        now = datetime.now(timezone.utc)

        attempt = AttemptData(
            userID=userID,
            kidIndex=kidIndex,
            quizID=quizID,
            deviceType=deviceType,
            device=device,
            attempts_count=stats.attempts_count,
            createdAt=now,
            updatedAt=now
        )

        attempt.init_answers(num_questions)
        attempt.start_time = now
        attempt.save()

        return {"message": "Attempt created", "attempt_id": str(attempt.id)}, 201

    except ValidationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 500


def update_attempt(data):
    try:
        attempt_id = data.get("attempt_id")
        question_index = data.get("question_index")
        is_correct = int(data.get("is_correct", 0))
        hint_used = int(data.get("hint_used", 0))
        is_wrong = int(data.get("is_wrong", 0))
        is_starting = bool(data.get("is_starting", False))
        duration = int(data.get("duration", 0))

        if not ObjectId.is_valid(attempt_id):
            return {"error": "Invalid attempt_id"}, 400

        attempt = AttemptData.objects(id=ObjectId(attempt_id)).first()
        if not attempt:
            return {"error": "Attempt not found"}, 404
        
        if attempt.completed or attempt.failed or attempt.aborted or attempt.timeout:
            return {"message": "Attempt already completed"}, 400

        num_questions = len(attempt.answers)
        if question_index is None or question_index < 0 or question_index >= num_questions:
            return {"error": f"Index {question_index} is invalid"}, 400

        if question_index > 0 and attempt.answers[question_index - 1].correct_answer == 0:
            return {"error": f"You must first answer question {question_index - 1}"}, 400

        if attempt.answers[question_index].correct_answer == 1:
            return {"error": f"Question {question_index} is already correct"}, 400

        now = datetime.now(timezone.utc)
        answer = attempt.answers[question_index]

        if is_starting:
            qa = QuestionAttempt(
                start_time=now,
            )
            answer.start_time = now
            answer.attempts.append(qa)
        else:
            if not answer.attempts or not answer.attempts[-1].start_time:
                return {"error": "No attempt in progress"}, 400

            qa = answer.attempts[-1]
            qa.end_time = now
            qa.is_correct = is_correct
            qa.is_wrong = is_wrong
            qa.hint_used = hint_used
            qa.duration = duration

            answer.end_time = now
            answer.attempts_count = len(answer.attempts)
            answer.correct_answer = sum(a.is_correct for a in answer.attempts)
            answer.wrong_answer = sum(a.is_wrong for a in answer.attempts)
            answer.hint_used = sum(a.hint_used for a in answer.attempts)
            answer.duration = sum(a.duration for a in answer.attempts)

        correct_answers = sum(ans.correct_answer for ans in attempt.answers)
        total_wrong_attempts = sum(ans.wrong_answer for ans in attempt.answers)

        if correct_answers == num_questions:
            attempt.completed = 1
            attempt.end_time = now
        elif total_wrong_attempts >= 3:
            attempt.failed = 1
            attempt.end_time = now

        attempt.duration = sum(ans.duration for ans in attempt.answers)
        attempt.updatedAt = now
        attempt.score, attempt.success_rate = calculate_score(attempt.answers, attempt.attempts_count)
        attempt.answered_questions = correct_answers

        attempt.save()

        status = (
            "completed" if attempt.completed else
            "failed" if attempt.failed else
            "aborted" if getattr(attempt, "aborted", 0) else
            "in_progress"
        )

        response = {"message": "Answer updated", "status": status, "attempt_id": str(attempt.id)}
        if not is_starting:
            response["score"] = attempt.score
        return response, 200

    except ValidationError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": str(e)}, 500


def abandon_attempt(data):
    attempt_id = data.get("attempt_id")
    if not attempt_id or not ObjectId.is_valid(attempt_id):
        return {"error": "Invalid attempt_id"}, 400

    attempt = AttemptData.objects(id=ObjectId(attempt_id)).first()
    if not attempt:
        return {"error": "Attempt not found"}, 404

    if attempt.completed or attempt.failed or attempt.aborted or attempt.timeout:
        return {"message": "Attempt already completed"}, 400

    attempt.aborted = 1
    attempt.end_time = datetime.now(timezone.utc)
    attempt.save()
    return {"message": "Quiz abandoned", "attempt_id": str(attempt.id)}, 200


def mark_timeout_attempts():
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    attempts = AttemptData.objects(
        completed=0, failed=0, aborted=0, timeout=0,
        start_time__lt=one_hour_ago
    )
    for attempt in attempts:
        attempt.timeout = 1
        attempt.end_time = attempt.start_time + timedelta(hours=1)
        attempt.time_spent = 3600
        attempt.save()


def recalculate_scores():
    try:
        attempts = AttemptData.objects()
        for attempt in attempts:
            attempt.score, attempt.success_rate = calculate_score(attempt.answers, attempt.attempts_count)
            attempt.save()
        return {"message": "Scores recalculated"}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def get_all_attempts():
    return [mongo_to_dict(a) for a in AttemptData.objects()], 200


def get_attempt_by_id(attempt_id):
    try:
        attempt = AttemptData.objects(id=ObjectId(attempt_id)).first()
        if not attempt:
            return {"error": "Attempt not found"}, 404
        return mongo_to_dict(attempt), 200
    except Exception as e:
        return {"error": str(e)}, 400


def get_attempts_per_kid(user_id, kid_index, from_date, to_date):
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
    return results, 200


def get_attempts_per_week(user_id, kid_index, start_date, end_date):
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
    return results, 200


def get_attempts_per_month(user_id, kid_index, start_date, end_date):
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
    return results, 200






















