from flask import jsonify, request
from controllers.accountController import get_kids_names
from models.attempt import AttemptData
import requests
from datetime import datetime, timedelta
from collections import defaultdict


# ---------- API pour récupérer les métadonnées des quiz ----------
def get_quizzes_metadata(quiz_ids):
    url = "http://48.216.249.114:8080/api/getquizesmetadata"
    payload = {"quizIds": quiz_ids}
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        quizzes_dict = response.json()
        return quizzes_dict
    except requests.exceptions.RequestException as e:
        print("Erreur API:", e)
        return {}

# ---------- Filtrage global ----------
def filter_attempts(grade=None, subject=None, period=7):
    since = datetime.now() - timedelta(days=period)
    query = {"start_time__gte": since}
    attempts_queryset = AttemptData.objects(**query)
    attempts = [a.to_mongo().to_dict() for a in attempts_queryset]

    # Récupérer métadonnées quiz
    quiz_ids = list(set(str(a.get("quizID")) for a in attempts if a.get("quizID")))
    quizzes = get_quizzes_metadata(quiz_ids)

    # Appliquer filtres quiz
    if grade:
        quizzes = {k: v for k, v in quizzes.items() if str(v.get("grade")) == grade}
    if subject:
        quizzes = {k: v for k, v in quizzes.items() if str(v.get("subject")) == subject}

    # Garde uniquement les attempts dont le quiz est encore dans quizzes
    attempts = [a for a in attempts if str(a.get("quizID")) in quizzes]

    return attempts, quizzes


# ---------- Stats globales ----------
def stats_overview(attempts):
    student_pairs = set()
    for a in attempts:
        user_id = a.get("userID")
        kid_index = a.get("kidIndex")
        if user_id is not None and kid_index is not None:
            student_pairs.add((user_id, kid_index))

    total_students = len(student_pairs)
    total_attempts = len(attempts)
    scores = [a.get("score") for a in attempts if a.get("score") is not None]
    average_score = (sum(scores) / len(scores)) if scores else 0
    times = [a.get("duration") for a in attempts if a.get("duration") is not None]
    average_time = (sum(times) / total_students) if total_students else 0

    return {
        "total_students": total_students,
        "total_attempts": total_attempts,
        "average_score": average_score,
        "average_time": average_time
    }


# ---------- Stats par niveau/matière/chapitre ----------
def stats_grades(attempts, quizzes_dict):
    grade_stats = {}
    for attempt in attempts:
        try:
            quiz_id = str(attempt.get("quizID", ""))
            if not quiz_id or quiz_id not in quizzes_dict:
                continue

            quiz_data = quizzes_dict[quiz_id]
            grade = quiz_data.get("grade", "Inconnu")
            subject = quiz_data.get("subject", "Inconnu")
            chapter = quiz_data.get("chapter", "Inconnu")

            score = float(attempt.get("score", 0))
            completed = 1 if attempt.get("completed", 0) == 1 else 0

            if grade not in grade_stats:
                grade_stats[grade] = {}
            if subject not in grade_stats[grade]:
                grade_stats[grade][subject] = {
                    "count": 0,
                    "completed": 0,
                    "total_score": 0.0,
                    "average_score": 0.0,
                    "chapters": {}
                }
            if chapter not in grade_stats[grade][subject]["chapters"]:
                grade_stats[grade][subject]["chapters"][chapter] = {
                    "count": 0,
                    "completed": 0,
                    "total_score": 0.0,
                    "average_score": 0.0
                }

            # Update stats
            subject_stats = grade_stats[grade][subject]
            subject_stats["count"] += 1
            subject_stats["completed"] += completed
            subject_stats["total_score"] += score

            chapter_stats = subject_stats["chapters"][chapter]
            chapter_stats["count"] += 1
            chapter_stats["completed"] += completed
            chapter_stats["total_score"] += score

        except (KeyError, TypeError, ValueError) as e:
            print(f"Erreur lors du traitement: {e}")
            continue

    # Moyennes finales
    for grade in grade_stats:
        for subject in grade_stats[grade]:
            subject_stats = grade_stats[grade][subject]
            if subject_stats["count"] > 0:
                subject_stats["average_score"] = round(subject_stats["total_score"] / subject_stats["count"], 4)
            del subject_stats["total_score"]

            for chapter in subject_stats["chapters"]:
                chapter_stats = subject_stats["chapters"][chapter]
                if chapter_stats["count"] > 0:
                    chapter_stats["average_score"] = round(chapter_stats["total_score"] / chapter_stats["count"], 4)
                del chapter_stats["total_score"]

    return grade_stats


def summary_by_grade(attempts, quizzes_dict):
    """
    Retourne un résumé par grade :
    {
        "Grade X": {
            "total_students": N,
            "total_attempts": M
        },
        ...
    }
    """
    summary = {}
    students_by_grade = {}

    for attempt in attempts:
        try:
            quiz_id = str(attempt.get("quizID", ""))
            if not quiz_id or quiz_id not in quizzes_dict:
                continue

            grade = quizzes_dict[quiz_id].get("grade", "Inconnu")

            if grade not in summary:
                summary[grade] = {
                    "total_students": 0,
                    "total_attempts": 0
                }
                students_by_grade[grade] = set()

            # incrémenter total_attempts
            summary[grade]["total_attempts"] += 1

            # stocker l'élève unique
            user_id = attempt.get("userID")
            kid_index = attempt.get("kidIndex")
            if user_id is not None and kid_index is not None:
                students_by_grade[grade].add((user_id, kid_index))

        except Exception as e:
            print(f"Erreur lors du traitement: {e}")
            continue

    # calcul final des total_students
    for grade, students in students_by_grade.items():
        summary[grade]["total_students"] = len(students)

    return summary


# ---------- Route unique ----------
def stats_all():
    grade = request.args.get('grade')
    subject = request.args.get('subject')
    period = int(request.args.get('period', 7))

    # Filtrage unique
    attempts, quizzes = filter_attempts(grade, subject, period)

    # Calculs
    overview = stats_overview(attempts)
    grade_stats_data = stats_grades(attempts, quizzes)

    return jsonify({
        "overview": overview,
        "grade_stats": grade_stats_data,
        "summary_by_grade": summary_by_grade(attempts, quizzes)
    })


# ---------- fonctions pour leaderboard avec meilleurs scores par quiz ----------

def get_unique_students_from_attempts():
    """Récupère tous les enfants distincts à partir des attempts filtrés avec leur score total"""
    
    grade = request.args.get('grade')
    subject = request.args.get('subject')
    period = int(request.args.get('period', 7))

    # Filtrage unique
    attempts, quizzes = filter_attempts(grade, subject, period)

    # D'abord, organiser les attempts par étudiant et par quiz
    student_quiz_scores = {}
    
    for attempt in attempts:
        user_id = attempt.get("userID")
        kid_index = attempt.get("kidIndex")
        quiz_id = str(attempt.get("quizID", ""))
        score = attempt.get("score", 0)
        
        if user_id is not None and kid_index is not None and quiz_id:
            student_key = (user_id, kid_index)
            
            if student_key not in student_quiz_scores:
                student_quiz_scores[student_key] = {}
            
            # Garder le meilleur score pour chaque quiz
            if quiz_id not in student_quiz_scores[student_key] or score > student_quiz_scores[student_key][quiz_id]:
                student_quiz_scores[student_key][quiz_id] = score
    
    # Maintenant calculer le score total pour chaque étudiant
    student_scores = []
    
    for student_key, quiz_scores in student_quiz_scores.items():
        user_id, kid_index = student_key
        total_score = sum(quiz_scores.values())
        quiz_count = len(quiz_scores)
        average_score = total_score / quiz_count if quiz_count > 0 else 0
        
        student_scores.append({
            "userID": user_id,
            "kidIndex": kid_index,
            "kidName": get_kids_names(user_id)[0][kid_index],
            "total_score": round(total_score,2),
            "quiz_count": quiz_count,
            "average_score": round(average_score, 2),
            "quiz_scores": quiz_scores  # Dictionnaire {quiz_id: meilleur_score}
        })

        student_scores = sorted(student_scores, key=lambda x: x["total_score"], reverse=True)

    
    return student_scores

   