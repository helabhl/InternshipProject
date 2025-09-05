from flask import jsonify, request
from datetime import datetime, timedelta, timezone
import pandas as pd
from models.attempt import AttemptData
from models.quiz import Quiz
from bson import ObjectId
from dateutil import parser


class PerformanceController:

    def get_messages_codes(userId, kidIndex):
        try:
            # --- Récupérer période ---
            from_str = request.args.get("from")
            to_str = request.args.get("to")
            period = request.args.get("period", "week")

            to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
            from_date = (
                to_date - timedelta(days=7) if period == "week" else
                to_date - timedelta(days=30) if period == "month" else
                (to_date - timedelta(days=60) if not from_str else datetime.fromisoformat(from_str))
            )

            # --- Charger attempts ---
            attempts = AttemptData.objects(
                userID=userId,
                kidIndex=kidIndex,
                start_time__gte=from_date,
                start_time__lte=to_date
            )

            if not attempts:
                return jsonify({
                    "userID": userId,
                    "kidIndex": kidIndex,
                    "from": from_date.isoformat(),
                    "to": to_date.isoformat(),
                    "period": period,
                    "achievements": [],
                    "alerts": [],
                    "recommendations": ["DEFAULT_NO_ACTIVITY"]
                }), 200

            kid_attempts = [a.to_mongo().to_dict() for a in attempts]
            quizzes = {str(q.id): q.to_mongo().to_dict() for q in Quiz.objects()}
            kid_subject_stats = subject_stats(kid_attempts, quizzes)

            # --- Calcul des métriques ---
            metrics = {
                "engagement": calculate_engagement(kid_attempts, from_date, to_date),
                "time_spent": total_time_spent(kid_attempts),
                "streak": calculate_streak(kid_attempts),
                "completion_rate": calculate_completion_rate(kid_attempts),
                "abandon_rate": abandonment_rate(kid_attempts),
                "progress": calculate_progress(kid_attempts, from_date, to_date, period=period),
                "mastery": calculate_mastery(kid_attempts, quizzes),
                "perseverance": calculate_perseverance(kid_attempts),
                "subject_balance": calculate_balance_score(kid_subject_stats),
                "recommendation": recommend_subject(kid_subject_stats)
            }

            # === Génération des codes ===
            achievements, alerts, recommendations = [], [], []
            days, total_days = metrics["engagement"]
            engagement_rate = days / total_days if total_days > 0 else 0

            if engagement_rate >= 0.8:
                achievements.append("ENGAGEMENT_HIGH")
            elif engagement_rate >= 0.6:
                achievements.append("ENGAGEMENT_GOOD")
            elif engagement_rate >= 0.4:
                achievements.append("ENGAGEMENT_AVERAGE")
            elif engagement_rate >= 0:
                alerts.append("ENGAGEMENT_LOW")

            streak = metrics["streak"]
            if streak >= 7:
                achievements.append("STREAK_7")
            elif streak >= 5:
                achievements.append("STREAK_5")
            elif streak >= 3:
                achievements.append("STREAK_3")

            completed, started = metrics["completion_rate"]
            if started > 0:
                rate = completed / started
                if rate >= 0.9:
                    achievements.append("COMPLETION_EXCELLENT")
                elif rate >= 0.7:
                    achievements.append("COMPLETION_GOOD")
                elif rate >= 0.5:
                    achievements.append("COMPLETION_AVERAGE")
                if rate < 0.5 and started > 3:
                    alerts.append("COMPLETION_LOW_ALERT")

            for subject, score in metrics["mastery"].items():
                if score >= 0.9:
                    achievements.append(f"MASTERY_EXCELLENT_{subject}")
                elif score >= 0.8:
                    achievements.append(f"MASTERY_GOOD_{subject}")
                elif score >= 0.7:
                    achievements.append(f"MASTERY_AVERAGE_{subject}")
                elif score < 0.5:
                    alerts.append(f"MASTERY_LOW_ALERT_{subject}")

            abandoned = metrics["abandon_rate"][0]
            if abandoned > 0:
                alerts.append("ABANDON_ALERT")

            perseverance = metrics["perseverance"]
            if perseverance["improved"] >= 5:
                achievements.append("PERSEVERANCE_STRONG")
            elif perseverance["improved"] >= 3:
                achievements.append("PERSEVERANCE_GOOD")
            elif perseverance["retries"] > 0:
                achievements.append("PERSEVERANCE_RETRIES")

            balance = metrics["subject_balance"]
            if balance < 40:
                recommendations.append("BALANCE_LOW")
            elif balance >= 80:
                achievements.append("BALANCE_GOOD")

            if metrics["recommendation"]:
                recommendations.append(f"RECOMMEND_{metrics['recommendation']}")

            total_minutes = metrics["time_spent"]
            if total_minutes >= 300:
                achievements.append("TIME_HIGH")
            elif total_minutes >= 180:
                achievements.append("TIME_MEDIUM")
            elif total_minutes > 0:
                alerts.append("TIME_LOW")

            if period == "week":
                achievements.append("INSPIRATION_WEEK")
            elif period == "month":
                achievements.append("INSPIRATION_MONTH")

            if not achievements:
                achievements.append("DEFAULT_ACHIEVEMENT")
            if not alerts:
                alerts.append("DEFAULT_ALERT")
            if not recommendations:
                recommendations.append("DEFAULT_RECOMMENDATION")

            return jsonify({
                "userID": userId,
                "kidIndex": kidIndex,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "period": period,
                "achievements": achievements,
                "alerts": alerts,
                "recommendations": recommendations
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @staticmethod
    def get_metrics(userId, kidIndex):
        try:
            from_str = request.args.get("from")
            to_str = request.args.get("to")
            from_date = datetime.fromisoformat(from_str) if from_str else None
            to_date = datetime.fromisoformat(to_str) if to_str else None

            query = {"userID": userId, "kidIndex": kidIndex}
            if from_date and to_date:
                query["start_time__gte"] = from_date
                query["start_time__lte"] = to_date

            attempts_list = AttemptData.objects(**query)
            kid_attempts = [a.to_mongo().to_dict() for a in attempts_list]
            quizzes = {str(q.id): q.to_mongo().to_dict() for q in Quiz.objects()}
            kid_subject_stats = subject_stats(kid_attempts, quizzes)

            metrics = {
                "engagement": calculate_engagement(kid_attempts, from_date, to_date),
                "time_spent": total_time_spent(kid_attempts),
                "streak": calculate_streak(kid_attempts),
                "completion_rate": calculate_completion_rate(kid_attempts),
                "abandon_rate": abandonment_rate(kid_attempts),
                "progress": calculate_progress(kid_attempts, from_date, to_date, period="week"),
                "mastery": calculate_mastery(kid_attempts, quizzes),
                "perseverance": calculate_perseverance(kid_attempts),
                "chapter_distribution": chapter_distribution(kid_attempts, quizzes),
                "persistent_failures": persistent_failures(kid_attempts),
                "subject_stats": kid_subject_stats,
                "subject_balance": calculate_balance_score(kid_subject_stats),
                "recommendation": recommend_subject(kid_subject_stats)
            }

            return jsonify(metrics), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500


    @staticmethod
    def get_performance(userId, kidIndex):
        try:
            from_str = request.args.get("from")
            to_str = request.args.get("to")
            to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
            from_date = to_date - timedelta(days=7) if not from_str else datetime.fromisoformat(from_str)

            attempts = AttemptData.objects(
                userID=userId,
                kidIndex=kidIndex,
                start_time__gte=from_date,
                start_time__lte=to_date
            )

            if not attempts:
                return jsonify({"message": "Aucune tentative"}), 200

            data = []
            for att in attempts:
                data.append({
                    "quizID": str(att.quizID),
                    "start_time": att.start_time,
                    "end_time": att.end_time,
                    "completed": att.completed,
                    "failed": att.failed,
                    "abandoned": att.aborted,
                    "score": getattr(att, "score", None),
                    "duration": att.duration
                })
            df = pd.DataFrame(data)

            lineplot = df[df["score"].notna()][["quizID", "score", "start_time"]] \
                .sort_values("start_time") \
                .to_dict(orient="records")

            df["weekday"] = df["start_time"].dt.strftime("%A")
            barplot = df.groupby("weekday")["quizID"].count().to_dict()

            result = {
                "lineplot": [
                    {"quizID": r["quizID"], "score": float(r["score"]), "start_time": r["start_time"].isoformat()}
                    for r in lineplot
                ],
                "barplot": {k: int(v) for k, v in barplot.items()}
            }

            return jsonify(result), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500



    # --- Score moyen par jour de la semaine ---
    def get_weekly_average_scores(userID, kidIndex):
        from_date = parser.isoparse(request.args.get("from"))
        to_date = parser.isoparse(request.args.get("to"))

        attempts = AttemptData.objects(
            userID=userID,
            kidIndex=kidIndex,
            createdAt__gte=from_date,
            createdAt__lte=to_date
        )

        # Initialisation
        jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        scores = {j: [] for j in jours}

        for att in attempts:
            day_index = att.createdAt.weekday()  # 0=Lundi, 6=Dimanche
            jour = jours[day_index]
            scores[jour].append(att.score)

        # Moyenne par jour
        data = [round(sum(v) / len(v), 2) if v else 0 for v in scores.values()]

        return jsonify({
            "labels": jours,
            "data": data
        })


    # --- Répartition des scores par matière ---
    def get_subject_distribution(userID, kidIndex):
        attempts = AttemptData.objects(userID=userID, kidIndex=kidIndex)

        subjects = {}
        for att in attempts:
            subj = get_subject_from_quiz(att, "subject", "Inconnu")
            subjects[subj] = subjects.get(subj, 0) + 1

        labels = list(subjects.keys())
        values = list(subjects.values())

        return jsonify({
            "labels": labels,
            "data": values
           
        })



####
#  PERFORMANCE CALCULATIONS
####


def calculate_engagement(attempts, from_date, to_date):
    """
    Nombre de jours de pratique entre from_date et to_date inclus.
    """
    practice_days = set()

    for attempt in attempts:
        start_time = attempt["start_time"]
        if from_date <= start_time <= to_date:
            practice_days.add(start_time.date())

    total_days = (to_date.date() - from_date.date()).days + 1
    return len(practice_days), total_days

def calculate_streak(attempts):
    """Plus longue série de quiz réussis (completed=1)"""
    # Trier les tentatives par date
    sorted_attempts = sorted(attempts, key=lambda x: x["start_time"])
    
    current_streak = 0
    max_streak = 0

    for attempt in sorted_attempts:
        if attempt.get("completed", 0) == 1:  # quiz réussi
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0  # rupture de la série
    
    return max_streak

def calculate_completion_rate(attempts):
    """Taux de complétion des quiz"""
    completed = sum(1 for a in attempts if a["completed"] == 1)
    total = len(attempts)
    
    return completed, total

def calculate_progress(attempts, from_date, to_date, period="week"):
    """
    Compare le nombre de quizzes complétés pendant la période courante
    (entre from_date et to_date) avec la période précédente.
    
    period : "week" ou "month"
    
    Retourne un ratio d'amélioration :
        >0  = progression (plus de quizzes que la période précédente)
         0  = stable
        <0  = régression (moins de quizzes)
    """

    if period == "week":
        delta = timedelta(days=7)
    elif period == "month":
        delta = timedelta(days=30)
    else:
        raise ValueError("Period doit être 'week' ou 'month'.")

    # Période courante
    current_period = [
        a for a in attempts
        if a.get("completed")
        and from_date <= a["start_time"] <= to_date
    ]

    # Période précédente
    prev_from = from_date - delta
    prev_to = from_date - timedelta(seconds=1)  # juste avant la période courante
    prev_period = [
        a for a in attempts
        if a.get("completed")
        and prev_from <= a["start_time"] <= prev_to
    ]

    current_count = len(current_period)
    prev_count = len(prev_period)

    if prev_count == 0:
        # pas d'activité précédente → 100% d'amélioration si progrès
        return 1.0 

    return (current_count - prev_count) / prev_count

def calculate_mastery(attempts, quizzes):
    """Sujets maîtrisés (score moyen > 70%)"""
    subject_scores = {}

    for attempt in attempts:

        subject = get_subject_from_quiz(attempt, quizzes)
        subject_scores.setdefault(subject, []).append(attempt.get("score", 0))

    # Garder seulement les sujets avec moyenne >= 80%
    mastery = {
        subject: sum(scores) / len(scores)
        for subject, scores in subject_scores.items()
        if sum(scores) / len(scores) >= 0.7
    }
    return mastery

def calculate_perseverance(attempts):
    """
    Retourne un dictionnaire avec:
    - 'retries': nombre de quiz retentés après échec
    - 'improved': nombre de quiz améliorés après échec
    """
    # Trier chronologiquement
    sorted_attempts = sorted(attempts, key=lambda x: x["start_time"])
    
    retries = 0
    improved = 0
    
    for i in range(1, len(sorted_attempts)):
        prev = sorted_attempts[i-1]
        current = sorted_attempts[i]
        
        # Même quiz (même quizID)
        if prev["quizID"] == current["quizID"]:
            # Échec précédent (abandoné ou score < 50%)
            if prev.get("aborted", 0) == 1 or prev.get("score", 0) < 0.5:
                retries += 1
                # Amélioration significative (+20% ou complétion)
                if (current.get("completed", 0) == 1 and 
                    (current.get("score", 0) - prev.get("score", 0) >= 0.2 or prev.get("completed", 0) == 0)):
                    improved += 1
    
    return {
        "retries": retries,
        "improved": improved,
        "perseverance_score": min(100, improved * 20)  # Score sur 100
    }

def get_subject_from_quiz(attempt, quizzes):
    """Retourne le subject du quiz correspondant à l'attempt"""

    # Récupération du quizID sous forme de string
    quiz_id = attempt.get("quizID")
    # Convertir ObjectId → str
    if isinstance(quiz_id, dict) and "$oid" in quiz_id:
        quiz_id = quiz_id["$oid"]
    elif isinstance(quiz_id, ObjectId):
        quiz_id = str(quiz_id)

    quiz = quizzes.get(str(quiz_id))
    return quiz.get("subject", "Inconnu") if quiz else "Inconnu"

def subject_stats(attempts, quizzes):
    """
    Retourne un dictionnaire avec:
    - 'subject_distribution': répartition par matière
    """
    subject_stats = {}
    score_accumulator = {}  # ✅ accumule les scores sans stocker dans subject_stats

    for attempt in attempts:
        subject = get_subject_from_quiz(attempt, quizzes)

        if subject not in subject_stats:
            subject_stats[subject] = {
                "count": 0,
                "completed": 0,
                "average_score": 0
            }
            score_accumulator[subject] = 0

        # Incrémenter les stats
        subject_stats[subject]["count"] += 1
        if attempt.get("completed", 0) == 1:
            subject_stats[subject]["completed"] += 1
            score_accumulator[subject] += attempt.get("score", 0)

    # Calcul des moyennes
    for subject, stats in subject_stats.items():
        if stats["count"] > 0:
            stats["average_score"] = (
                score_accumulator[subject] / stats["count"]
            )
    
    return subject_stats

def calculate_balance_score(subject_stats):
    """
    Score basé sur la répartition des attempts entre les matières
    """
    total_attempts = sum(s["count"] for s in subject_stats.values())
    if total_attempts == 0:
        return 0
    max_ratio = max(s["count"] / total_attempts for s in subject_stats.values())
    return int(min(100, 100 - (max_ratio * 50)))

def recommend_subject(subject_stats):
    """
    Retourne la matière la moins travaillée (et score le plus faible en cas d'égalité)
    """
    if not subject_stats:
        return "Aucune"
    return min(subject_stats.items(), key=lambda x: (x[1]["count"], x[1]["average_score"]))[0]

def abandonment_rate(attempts):
    total = len(attempts)
    abandoned = sum(1 for a in attempts if a.get("abandoned") == 1)
    return abandoned, total if total else 0

def chapter_distribution(attempts, quizzes):
    """
    Retourne une distribution imbriquée :
    {
        subject: {
            chapter: {"attempts": int, "average_score": float}
        }
    }
    """
    distribution = {}

    for a in attempts:
        quiz = quizzes.get(str(a.get("quizID")))
        subject = quiz.get("subject", "inconnu") if quiz else "inconnu"
        chapter = quiz.get("chapter", "inconnu") if quiz else "inconnu"

        if subject not in distribution:
            distribution[subject] = {}

        if chapter not in distribution[subject]:
            distribution[subject][chapter] = {"attempts": 0, "total_score": 0}

        distribution[subject][chapter]["attempts"] += 1
        distribution[subject][chapter]["total_score"] += a.get("score", 0)

    # Calcul des moyennes
    for subject, chapters in distribution.items():
        for chapter, stats in chapters.items():
            stats["average_score"] = (
                stats["total_score"] / stats["attempts"] if stats["attempts"] > 0 else 0
            )
            del stats["total_score"]

    return distribution

def total_time_spent(attempts):
    total_time = 0
    for a in attempts:
        if a.get("timeout") != 1 and a.get("duration"):
            total_time += a.get("duration")
    return total_time/ 60  # minutes

def persistent_failures(attempts):
    failed_quizzes = {}
    for a in attempts:
        if a.get("failed") == 1 or (a.get("completed") == 1 and a.get("score", 0) < 0.4):
            quiz_id = str(a.get("quizID"))
            failed_quizzes[quiz_id] = failed_quizzes.get(quiz_id, 0) + 1
    # filtrer ceux >=3
    return {k: v for k, v in failed_quizzes.items() if v >= 3}
