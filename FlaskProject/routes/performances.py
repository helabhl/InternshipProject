from flask import Blueprint, request, jsonify
from models.attempt import AttemptData
from models.quiz import Quiz
from bson import ObjectId
from mongoengine.errors import ValidationError
from datetime import datetime, timedelta, timezone
import pandas as pd
import random


performance_bp = Blueprint("performancesdata", __name__)
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






def calculate_perseverance(attempts, quizzes):
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
            if prev.get("abandoned", 0) == 1 or prev.get("score", 0) < 0.5:
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
        if a.get("completed"):
            start, end = a.get("start_time"), a.get("end_time")
            if start and end:
                total_time += (end - start).total_seconds() / 60  # minutes
    return total_time

def persistent_failures(attempts):
    failed_quizzes = {}
    for a in attempts:
        if a.get("failed") == 1 or (a.get("completed") == 1 and a.get("score", 0) < 0.4):
            quiz_id = str(a.get("quizID"))
            failed_quizzes[quiz_id] = failed_quizzes.get(quiz_id, 0) + 1
    # filtrer ceux >=3
    return {k: v for k, v in failed_quizzes.items() if v >= 3}

@performance_bp.route("/<userId>/kids/<kidIndex>/messagesCodes", methods=["GET"])
def get_messages_codes(userId, kidIndex):
    try:
        # Récupérer période
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        period = request.args.get("period", "week")  # week | month

        to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
        from_date = (
            to_date - timedelta(days=7) if period == "week" else
            to_date - timedelta(days=30) if period == "month" else
            (to_date - timedelta(days=60) if not from_str else datetime.fromisoformat(from_str))
        )

        # Charger les attempts
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

        # Convertir attempts
        kid_attempts = [a.to_mongo().to_dict() for a in attempts]
        quizzes = {str(q.id): q.to_mongo().to_dict() for q in Quiz.objects()}
        kid_subject_stats = subject_stats(kid_attempts, quizzes)

        # Calculer métriques
        metrics = {
            "engagement": calculate_engagement(kid_attempts, from_date, to_date),
            "time_spent": total_time_spent(kid_attempts),
            "streak": calculate_streak(kid_attempts),
            "completion_rate": calculate_completion_rate(kid_attempts),
            "abandon_rate": abandonment_rate(kid_attempts),
            "progress": calculate_progress(kid_attempts, from_date, to_date, period=period),
            "mastery": calculate_mastery(kid_attempts, quizzes),
            "perseverance": calculate_perseverance(kid_attempts, quizzes),
            "subject_balance": calculate_balance_score(kid_subject_stats),
            "recommendation": recommend_subject(kid_subject_stats)
        }

        # === Génération des codes ===
        achievements = []
        alerts = []
        recommendations = []

        # Engagement
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
        
        # Streak
        streak = metrics["streak"]
        if streak >= 7:
            achievements.append("STREAK_7")
        elif streak >= 5:
            achievements.append("STREAK_5")
        elif streak >= 3:
            achievements.append("STREAK_3")

        # Completion
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

        # Mastery
        for subject, score in metrics["mastery"].items():
            if score >= 0.9:
                achievements.append(f"MASTERY_EXCELLENT_{subject}")
            elif score >= 0.8:
                achievements.append(f"MASTERY_GOOD_{subject}")
            elif score >= 0.7:
                achievements.append(f"MASTERY_AVERAGE_{subject}")
            elif score < 0.5:
                alerts.append(f"MASTERY_LOW_ALERT_{subject}")

        # Abandons
        abandoned = metrics["abandon_rate"][0]
        if abandoned > 0:
            alerts.append("ABANDON_ALERT")

        # Perseverance
        perseverance = metrics["perseverance"]
        if perseverance["improved"] >= 5:
            achievements.append("PERSEVERANCE_STRONG")
        elif perseverance["improved"] >= 3:
            achievements.append("PERSEVERANCE_GOOD")
        elif perseverance["retries"] > 0:
            achievements.append("PERSEVERANCE_RETRIES")

        # Balance des matières
        balance = metrics["subject_balance"]
        if balance < 40:
            recommendations.append("BALANCE_LOW")
        elif balance >= 80:
            achievements.append("BALANCE_GOOD")

        # Recommandation principale
        if metrics["recommendation"]:
            recommendations.append(f"RECOMMEND_{metrics['recommendation']}")

        # Time spent
        total_minutes = metrics["time_spent"]
        if total_minutes >= 300:
            achievements.append("TIME_HIGH")
        elif total_minutes >= 180:
            achievements.append("TIME_MEDIUM")
        elif total_minutes > 0:
            alerts.append("TIME_LOW")

        # Inspiration selon période
        if period == "week":
            achievements.append("INSPIRATION_WEEK")
        elif period == "month":
            achievements.append("INSPIRATION_MONTH")

        # Valeurs par défaut
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

@performance_bp.route("/metrics/<userId>/kids/<kidIndex>", methods=["GET"])
def get_kid_metrics(userId, kidIndex):
    try:
        # 🔹 Récupérer période
        from_str = request.args.get("from")
        to_str = request.args.get("to")

        from_date = datetime.fromisoformat(from_str) if from_str else None
        to_date = datetime.fromisoformat(to_str) if to_str else None

        # 🔹 Charger attempts de cet enfant
        query = {
            "userID": userId,
            "kidIndex": kidIndex 
        }
        if from_date and to_date:
            query["start_time__gte"] = from_date
            query["start_time__lte"] = to_date

        attempts_list = AttemptData.objects(**query)

        # 🔹 Convertir en dict si besoin
        kid_attempts = [a.to_mongo().to_dict() for a in attempts_list]

        # 🔹 Charger les quizzes
        quizzes = {str(q.id): q.to_mongo().to_dict() for q in Quiz.objects()}


        kid_subject_stats = subject_stats(kid_attempts, quizzes)

        # 🔹 Calcul des métriques
        metrics = {
            "engagement": calculate_engagement(kid_attempts, from_date, to_date),
            "time_spent":total_time_spent(kid_attempts),
            "streak": calculate_streak(kid_attempts),
            "completion_rate": calculate_completion_rate(kid_attempts),
            "abandon_rate":abandonment_rate(kid_attempts),
            "progress": calculate_progress(kid_attempts, from_date, to_date, period="week"),
            "mastery": calculate_mastery(kid_attempts, quizzes),
            "perseverance": calculate_perseverance(kid_attempts, quizzes),
            "chapter_distribution":chapter_distribution(kid_attempts, quizzes),
            "persistent_failures":persistent_failures(kid_attempts),
            "subject_stats": kid_subject_stats,
            "subject_balance": calculate_balance_score(kid_subject_stats),
            "recommendation": recommend_subject(kid_subject_stats)
        }

        return jsonify(metrics), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@performance_bp.route("/performances/<user_id>/<kidId>", methods=["GET"])
def get_performance(user_id,kidId):
    try:
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
        from_date = to_date - timedelta(days=7) if not from_str else datetime.fromisoformat(from_str)

        attempts = AttemptData.objects(
            userID=user_id,
            kidIndex=kidId,
            start_time__gte=from_date,
            start_time__lte=to_date
        )

        if not attempts:
            return jsonify({"message": "Aucune tentative"}), 200

        # Convertir en dataframe pour analyse
        data = []
        for att in attempts:
            data.append({
                "quizID": str(att.quizID),
                "start_time": att.start_time,
                "end_time": att.end_time,
                "completed": att.completed,
                "failed": att.failed,
                "abandoned": att.abandoned,
                "score": getattr(att, "score", None),
                "time_spent": (att.end_time - att.start_time).total_seconds() if att.end_time else 0
            })
        df = pd.DataFrame(data)



        # --- Lineplot (scores dans le temps) ---
        lineplot = df[df["score"].notna()][["quizID", "score", "start_time"]] \
            .sort_values("start_time") \
            .to_dict(orient="records")

        # --- Barplot (quizzes par jour de semaine) ---
        df["weekday"] = df["start_time"].dt.strftime("%A")  # Lundi, Mardi...
        barplot = df.groupby("weekday")["quizID"].count().to_dict()

        result = {
           
            "lineplot": [
                {
                    "quizID": r["quizID"],
                    "score": float(r["score"]),
                    "start_time": r["start_time"].isoformat()
                } for r in lineplot
            ],
            "barplot": {k: int(v) for k, v in barplot.items()}
        }


        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500    







##############

@performance_bp.route("/attempts/<userId>/kids/<kidIndex>/motivations", methods=["GET"])
def get_motivationnal_messages(userId, kidIndex):
    try:
        # Récupérer période (from/to en query string)
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
        from_date = to_date - timedelta(days=60) if not from_str else datetime.fromisoformat(from_str)

        # Charger les attempts de cet enfant
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
                "messages": ["🌟 Aucun quiz trouvé pour cette période, continuez vos efforts !"]
            }), 200

        # 🔹 Convertir attempts + charger quizzes
        kid_attempts = [a.to_mongo().to_dict() for a in attempts]
        quizzes = {str(q.id): q.to_mongo().to_dict() for q in Quiz.objects()}
        
        kid_subject_stats = subject_stats(kid_attempts, quizzes)

        # 🔹 Calculer metrics directement
        metrics = {
            "engagement": calculate_engagement(kid_attempts, from_date, to_date),
            "time_spent":total_time_spent(kid_attempts),
            "streak": calculate_streak(kid_attempts),
            "completion_rate": calculate_completion_rate(kid_attempts),
            "abandon_rate":abandonment_rate(kid_attempts),
            "progress": calculate_progress(kid_attempts, from_date, to_date, period="week"),
            "mastery": calculate_mastery(kid_attempts, quizzes),
            "perseverance": calculate_perseverance(kid_attempts, quizzes),
            "chapter_distribution":chapter_distribution(kid_attempts, quizzes),
            "persistent_failures":persistent_failures(kid_attempts),
            "subject_stats": kid_subject_stats,
            "subject_balance": calculate_balance_score(kid_subject_stats),
            "recommendation": recommend_subject(kid_subject_stats)
        }
        messages = []  # Initialiser une liste vide par défaut
        
        # Vérifier que metrics existe et est un dictionnaire
        
        try:
            # 1. Engagement et régularité
            days, total_days = metrics["engagement"]
            if days >= 5:
                messages.append("🔥 Engagement exceptionnel ! 5 jours ou plus de pratique cette semaine !")
            elif days >= 3:
                messages.append(f"🌟 Bonne régularité ! {days} jours de pratique sur {total_days} !")
            elif days > 0:
                messages.append(f"🌱 Commence à prendre l'habitude ! {days} jour(s) de pratique cette semaine.")

            # 2. Performance (scores élevés)
            high, total = metrics["high_scores"]    
            if total > 0:
                ratio = high / total
                if ratio >= 0.8:
                    messages.append(f"🎯 Maîtrise impressionnante ! {high}/{total} quiz à plus de 80% !")
                elif ratio >= 0.6:
                    messages.append(f"👍 Bonnes performances ! {high} quiz très réussis !")
                elif ratio > 0:
                    messages.append(f"✨ {high} belle(s) réussite(s) cette semaine !")

            # 3. Série de succès
            streak = metrics["streak"]
            if streak >= 5:
                messages.append(f"🚀 Série incroyable ! {streak} quiz réussis d'affilée !")
            elif streak >= 3:
                messages.append(f"🔥 En plein flow ! {streak} réussites consécutives !")

            # 4. Complétion des quiz
            completed, started = metrics["completion_rate"]
            if started > 0:
                rate = completed / started
                if rate >= 0.9:
                    messages.append(f"💯 Persévérant ! {completed} quiz terminés sur {started} commencés !")
                elif rate >= 0.7:
                    messages.append(f"📚 Bon taux de complétion : {int(rate*100)}% des quiz finis !")
                elif completed > 0:
                    messages.append(f"✊ Continue comme ça ! {completed} quiz terminés cette semaine.")

            # 5. Progression
            progress = metrics["progress"]
            if progress > 0.15:
                messages.append(f"📈 Progression fulgurante ! +{progress*100:.0f}% de scores en 2 semaines !")
            elif progress > 0.05:
                messages.append(f"↗️ En nette amélioration ! +{progress*100:.0f}% de progression")
            elif progress > 0:
                messages.append(f"🌱 Légère amélioration des scores (+{progress*100:.0f}%)")

            # 6. Maîtrise des sujets
            mastered = metrics["mastery"]
            if len(mastered) >= 3:
                subjects = ", ".join(mastered.keys())
                messages.append(f"🏆 Expert multisujets : maîtrise parfaite en {subjects} !")
            elif mastered:
                subject, score = next(iter(mastered.items()))
                messages.append(f"👑 Maîtrise excellente en {subject} ({score*100:.0f}%) !")

            # 7. Vitesse d'exécution
            speed_improv = metrics["speed_improvement"]
            if speed_improv > 0.2:
                messages.append(f"⚡ Rapidité décuplée ! {speed_improv*100:.0f}% plus rapide !")
            elif speed_improv > 0.1:
                messages.append(f"⏱️ Temps de réponse amélioré de {speed_improv*100:.0f}%")


            # 9. Persévérance
            perseverance = metrics["perseverance"]
            if perseverance["improved"] >= 3:
                messages.append(f"🧠 Persévérance exemplaire ! {perseverance['improved']} retentatives réussies")
            elif perseverance["retries"] > 0:
                messages.append(f"💪 {perseverance['retries']} réussite(s) après échec")

            # 10. Équilibre des matières
            balance = metrics["subject_balance"]
            if balance["balance_score"] >= 80:
                messages.append("🌈 Équilibre parfait entre les matières !")
            elif len(balance["subject_distribution"]) >= 3:
                messages.append(f"📚 Variété : {len(balance['subject_distribution'])} matières étudiées")
            if balance["balance_score"] < 40:
                messages.append(f"🔍 Conseil : essayez plus de {balance['recommendation']}")
            # Si aucun message généré
            if not messages:
                messages.append("🌱 Tous les progrès commencent petit - continuez !")
                
        except Exception as e:
            print(f"Erreur dans la génération des messages: {e}")
            messages = ["✨ Votre enfant fait des progrès chaque jour !"]

        return jsonify({
            "userID": userId,
            "kidIndex": kidIndex,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "messages": messages
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@performance_bp.route("/attempts/<userId>/kids/<kidIndex>/messages", methods=["GET"])
def get_messages(userId, kidIndex):
    try:
        # Récupérer période
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
        from_date = to_date - timedelta(days=60) if not from_str else datetime.fromisoformat(from_str)

        # Charger les attempts
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
                "achievements": [],
                "alerts": [],
                "recommendations": ["🌟 Aucun quiz trouvé pour cette période, continuez vos efforts !"]
            }), 200

        # Convertir attempts
        kid_attempts = [a.to_mongo().to_dict() for a in attempts]
        quizzes = {str(q.id): q.to_mongo().to_dict() for q in Quiz.objects()}
        kid_subject_stats = subject_stats(kid_attempts, quizzes)

        # Calculer métriques
        metrics = {
            "engagement": calculate_engagement(kid_attempts, from_date, to_date),
            "time_spent": total_time_spent(kid_attempts),
            "streak": calculate_streak(kid_attempts),
            "completion_rate": calculate_completion_rate(kid_attempts),
            "abandon_rate": abandonment_rate(kid_attempts),
            "progress": calculate_progress(kid_attempts, from_date, to_date, period="week"),
            "mastery": calculate_mastery(kid_attempts, quizzes),
            "perseverance": calculate_perseverance(kid_attempts, quizzes),
            "chapter_distribution": chapter_distribution(kid_attempts, quizzes),
            "persistent_failures": persistent_failures(kid_attempts),
            "subject_stats": kid_subject_stats,
            "subject_balance": calculate_balance_score(kid_subject_stats),
            "recommendation": recommend_subject(kid_subject_stats)
        }

        # Trois catégories
        achievements = []
        alerts = []
        recommendations = []

        try:
            # === Engagement ===
            days, total_days = metrics["engagement"]
            if days >= 5:
                achievements.append("🔥 Engagement exceptionnel ! 5 jours ou plus de pratique cette semaine !")
            elif days >= 3:
                achievements.append(f"🌟 Bonne régularité ! {days} jours de pratique sur {total_days}.")
            elif days > 0:
                achievements.append(f"🌱 Début prometteur : {days} jour(s) de pratique cette semaine.")

            # === Séries ===
            streak = metrics["streak"]
            if streak >= 5:
                achievements.append(f"🚀 Série incroyable ! {streak} quiz réussis d'affilée !")
            elif streak >= 3:
                achievements.append(f"🔥 En plein flow ! {streak} réussites consécutives !")

            # === Complétion ===
            completed, started = metrics["completion_rate"]
            if started > 0:
                rate = completed / started
                if rate >= 0.9:
                    achievements.append(f"💯 Persévérance remarquable : {completed}/{started} quiz complétés.")
                elif rate >= 0.7:
                    achievements.append(f"📚 Bon taux de complétion : {int(rate*100)}% des quiz finis.")
                elif completed > 0:
                    achievements.append(f"✊ Détermination : {completed} quiz complétés.")

            # === Maîtrise ===
            for subject, score in metrics["mastery"].items():
                if score >= 0.8:
                    achievements.append(f"👑 Maîtrise excellente en {subject} ({score*100:.0f}%).")
                elif score < 0.5:
                    alerts.append(f"⚠️ Faible maîtrise en {subject} ({score*100:.0f}%).")

            # === Abandons ===
            abandoned = metrics["abandon_rate"][1]
            if abandoned > 0:
                alerts.append(f"⚠️ {abandoned} quiz abandonnés cette période. Essaye de les terminer.")

            # === Progression ===
            progress = metrics["progress"]
            if progress > 0.15:
                achievements.append(f"📈 Progression fulgurante : +{progress*100:.0f}% de scores.")
            elif progress > 0.05:
                achievements.append(f"↗️ En nette amélioration : +{progress*100:.0f}%.")
            elif progress == 0:
                recommendations.append("🔑 Continue à pratiquer pour enclencher une progression visible.")

            # === Persévérance ===
            perseverance = metrics["perseverance"]
            if perseverance["improved"] >= 3:
                achievements.append(f"🧠 Persévérance exemplaire : {perseverance['improved']} retentatives réussies.")
            elif perseverance["retries"] > 0:
                achievements.append(f"💪 {perseverance['retries']} réussite(s) après échec.")

            # === Balance des matières ===
            balance = metrics["subject_balance"]
            if balance < 40:
                recommendations.append("📌 Conseil : diversifie tes matières pour un meilleur équilibre.")
            elif balance >= 80:
                achievements.append("🌈 Excellent équilibre entre les matières étudiées.")

            # === Recommandation principale ===
            if metrics["recommendation"]:
                recommendations.append(f"🎯 Priorité : concentre-toi sur {metrics['recommendation']}.")

            # Valeurs par défaut si rien
            if not achievements:
                achievements.append("🌟 Continue tes efforts, chaque progrès compte !")
            if not alerts:
                alerts.append("✅ Aucun problème majeur détecté.")
            if not recommendations:
                recommendations.append("📖 Continue sur ta lancée, tout va bien !")

        except Exception as e:
            print(f"Erreur génération messages: {e}")
            achievements.append("✨ Ton enfant fait des progrès chaque jour !")

        return jsonify({
            "userID": userId,
            "kidIndex": kidIndex,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "achievements": achievements,
            "alerts": alerts,
            "recommendations": recommendations
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/attempts/<userId>/kids/<kidIndex>/messagesAr", methods=["GET"])
def get_messages_arabe(userId, kidIndex):
    try:
        # Récupérer période
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        period = request.args.get("period", "week")  # Nouveau paramètre pour la période
        
        to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
        from_date = to_date - timedelta(days=7) if period == "week" else (to_date - timedelta(days=30) if period == "month" else (to_date - timedelta(days=60) if not from_str else datetime.fromisoformat(from_str)))

        # Déterminer le libellé de période pour les messages
        period_label = "هذا الأسبوع" if period == "week" else "هذا الشهر"

        # Charger les attempts
        attempts = AttemptData.objects(
            userID=userId,
            kidIndex=kidIndex,
            start_time__gte=from_date,
            start_time__lte=to_date
        )

        if not attempts:
            motivation_phrases = [
                "كل رحلة عظيمة تبدأ بخطوة واحدة، لنبدأ رحلة التعلم معاً!",
                "النجاح هو مجموع الجهود الصغيرة المتكررة يوماً بعد يوم، لنبدأ اليوم!",
                "العقول العظيمة لديها أهداف، والآخرون لديهم أمنيات. حدد هدفك اليوم!"
            ]
            return jsonify({
                "userID": userId,
                "kidIndex": kidIndex,
                "from": from_date.isoformat(),
                "to": to_date.isoformat(),
                "period": period,
                "achievements": [],
                "alerts": [],
                "recommendations": [f"لم يتم العثور على اختبارات لـ{period_label}، {random.choice(motivation_phrases)}"]
            }), 200

        # Convertir attempts
        kid_attempts = [a.to_mongo().to_dict() for a in attempts]
        quizzes = {str(q.id): q.to_mongo().to_dict() for q in Quiz.objects()}
        kid_subject_stats = subject_stats(kid_attempts, quizzes)

        # Calculer métriques
        metrics = {
            "engagement": calculate_engagement(kid_attempts, from_date, to_date),
            "time_spent": total_time_spent(kid_attempts),
            "streak": calculate_streak(kid_attempts),
            "completion_rate": calculate_completion_rate(kid_attempts),
            "abandon_rate": abandonment_rate(kid_attempts),
            "progress": calculate_progress(kid_attempts, from_date, to_date, period=period),
            "mastery": calculate_mastery(kid_attempts, quizzes),
            "perseverance": calculate_perseverance(kid_attempts, quizzes),
            "chapter_distribution": chapter_distribution(kid_attempts, quizzes),
            "persistent_failures": persistent_failures(kid_attempts),
            "subject_stats": kid_subject_stats,
            "subject_balance": calculate_balance_score(kid_subject_stats),
            "recommendation": recommend_subject(kid_subject_stats)
        }

        # Trois catégories
        achievements = []
        alerts = []
        recommendations = []

        try:
            # === Engagement ===
            days, total_days = metrics["engagement"]
            engagement_rate = days/total_days if total_days > 0 else 0
            
            if engagement_rate >= 0.8:
                achievements.append(f"مذهل! التزام رائع {period_label} - تم التدرب في {days} من أصل {total_days} يوم! 🌟")
            elif engagement_rate >= 0.6:
                achievements.append(f"أداء متميز! واظبت على التعلم في {days} يوم {period_label}. استمر في هذا النجاح! 💪")
            elif engagement_rate >= 0.4:
                achievements.append(f"بداية قوية! {days} أيام من التعلم {period_label}. يمكننا زيادة هذا العدد! ✨")
            elif engagement_rate > 0:
                alerts.append(f"لاحظنا مشاركة متواضعة {period_label} ({days} أيام فقط). التعلم المنتظم هو مفتاح النجاح!")
            else:
                alerts.append(f"لم يتم تسجيل أي نشاط تعليمي {period_label}. كل يوم جديد هو فرصة للتعلم والتقدم!")

            # === Séries ===
            streak = metrics["streak"]
            if streak >= 7:
                achievements.append(f"قوة إرادة استثنائية! {streak} اختبارات ناجحة متتالية! أنت تبني عادات رائعة! 🏆")
            elif streak >= 5:
                achievements.append(f"تقدم مذهل! {streak} نجاحات متتالية. الزخم الذي تبنيّه سيوصلك إلى القمة! 🔥")
            elif streak >= 3:
                achievements.append(f"في حالة تدفق! {streak} نجاحات متتالية. استمر في هذا الأداء الرائع! ⚡")

            # === Complétion ===
            completed, started = metrics["completion_rate"]
            if started > 0:
                rate = completed / started
                if rate >= 0.9:
                    achievements.append(f"مثابرة ملهمة! أتممت {completed} من أصل {started} اختبار {period_label}. الإصرار يصنع المعجزات! 🌈")
                elif rate >= 0.7:
                    achievements.append(f"معدل إنجاز رائع! {int(rate*100)}% من الاختبارات مكتملة. استمر في التركيز! 🎯")
                elif rate >= 0.5:
                    achievements.append(f"خطوات ثابتة نحو النجاح! أتممت {completed} اختبار {period_label}. يمكننا تحسين معدل الإكمال! 📊")
                elif completed > 0:
                    achievements.append(f"لقد بدأت رحلة التعلم! {completed} اختبار مكتمل {period_label}. فلنعمل على زيادة هذا العدد! 🌱")
                
                if rate < 0.5 and started > 3:
                    alerts.append(f"لديك {started-completed} اختبار غير مكتمل. الإنجاز الكامل يعزز فهمك للمواد!")

            # === Maîtrise ===
            mastery_achievements = []
            mastery_alerts = []
            
            for subject, score in metrics["mastery"].items():
                if score >= 0.9:
                    mastery_achievements.append(f"براعة استثنائية في {subject} ({score*100:.0f}%)! أنت تتقن هذا المجال بامتياز! 🥇")
                elif score >= 0.8:
                    mastery_achievements.append(f"تميز واضح في {subject} ({score*100:.0f}%). استمر في تطوير هذه المهارة! 🎓")
                elif score >= 0.7:
                    mastery_achievements.append(f"فهم قوي لـ{subject} ({score*100:.0f}%). أنت على الطريق الصحيح! 📚")
                elif score < 0.5:
                    mastery_alerts.append(f"هناك فرصة لتحسين فهمك لـ{subject} ({score*100:.0f}%). كل تحدي تعليمي هو فرصة للنمو! 🌱")
            
            achievements.extend(mastery_achievements)
            alerts.extend(mastery_alerts)

            # === Abandons ===
            abandoned = metrics["abandon_rate"][0]
            if abandoned > 0:
                alerts.append(f"لاحظنا {abandoned} اختبار غير مكتمل {period_label}. المحاولة حتى النهاية تبني قوة الإرادة!")

            # # === Progression ===
            # progress = metrics["progress"]
            # if progress > 0.5:
            #     achievements.append(f"تقدم مذهل! زاد نشاطك بنسبة {progress*100:.0f}% {period_label}. هذا يستحق الثناء! 🚀")
            # elif progress > 0.2:
            #     achievements.append(f"تحسن ملحوظ! زيادة بنسبة {progress*100:.0f}% في النشاط التعليمي. الزخم يصنع الفرق! 📈")
            # elif progress > 0:
            #     achievements.append(f"تقدم إيجابي! زيادة طفيفة في النشاط بنسبة {progress*100:.0f}%. كل خطوة مهمة! 👣")
            # elif progress < 0:
            #     alerts.append(f"انخفاض في النشاط بنسبة {abs(progress*100):.0f}%. العودة إلى الروتين التعليمي ستحدث الفرق!")

            # === Persévérance ===
            perseverance = metrics["perseverance"]
            if perseverance["improved"] >= 5:
                achievements.append(f"إصرار ملهم! {perseverance['improved']} نجاحات بعد محاولات سابقة. هذه الروح لا تقهر! 💫")
            elif perseverance["improved"] >= 3:
                achievements.append(f"عزيمة قوية! {perseverance['improved']} نجاحات بعد فشل سابق. التعلم من الأخطاء هو طريق النجاح! 🌟")
            elif perseverance["retries"] > 0:
                achievements.append(f"محاولات متكررة تعكس التصميم! {perseverance['retries']} محاولة تُظهر رغبة حقيقية في التعلم! 🔁")

            # === Balance des matières ===
            balance = metrics["subject_balance"]
            if balance < 40:
                recommendations.append("تنويع المواد الدراسية يعزز التعلم الشامل. جرب التركيز على مادة مختلفة في الجلسة القادمة! 🌈")
            elif balance >= 80:
                achievements.append("توازن رائع بين المواد! هذا التنوع يبني معرفة متكاملة. أحسنت! ⚖️")

            # === Recommandation principale ===
            if metrics["recommendation"]:
                recommendations.append(f"لتحقيق أقصى استفادة: نوصي بالتركيز على {metrics['recommendation']} في الفترة القادمة. 📌")

            # === Time Spent ===
            total_minutes = metrics["time_spent"]
            hours = total_minutes // 60
            minutes = round(total_minutes % 60)
            
            if total_minutes > 0:
                time_message = f"قضيت "
                if hours > 0:
                    time_message += f"{hours} ساعة و"
                time_message += f"{minutes} دقيقة في التعلم {period_label}. الاستثمار في المعرفة يدفع أفضل الفوائد! ⏳"
                
                if total_minutes >= 300:  # 5 hours or more
                    achievements.append(f"تفاني ملهم! {time_message}")
                elif total_minutes >= 180:  # 3 hours or more
                    achievements.append(f"التزام رائع! {time_message}")
                else:
                    achievements.append(f"جهد مقدر! {time_message}")

            # Messages d'inspiration supplémentaires basés sur la période
            inspirational_messages = {
                "week": [
                    "أسبوع من التقدم هو أسبوع من النجاح. استمر في البناء على هذا الزخم!",
                    "الأسابيع تتحد لتشكل أشهر النجاح. أنت تضع الأساس لمستقبل مشرق!",
                    "كل أسبوع يحمل فرصًا جديدة للنمو. استفد منها إلى أقصى حد!"
                ],
                "month": [
                    "الشهر الذي مضى هو شاهد على تقدمك. الشهر القادم يحمل إمكانيات لا حصر لها!",
                    "أشهر من التعلم المتسق تبني سنوات من النجاح. أنت على المسار الصحيح!",
                    "استمرارية جهودك الشهرية هي ما يصنع الفارق الحقيقي. استمر في العمل الجاد!"
                ]
            }
            
            # Ajouter un message d'inspiration aléatoire
            if period in inspirational_messages:
                achievements.append(random.choice(inspirational_messages[period]))

            # Valeurs par défaut si rien
            if not achievements:
                default_achievements = [
                    "كل جهد تبذله يبني مستقبلك. استمر في العمل بدأب! 🌱",
                    "رحلة التعلم مليئة بالتحديات والانتصارات. أنت تقوم بعمل رائع! ✨",
                    "التقدم قد يكون غير مرئي أحياناً، لكنه حقيقي. ثق في العملية! 📚"
                ]
                achievements.append(random.choice(default_achievements))
                
            if not alerts:
                alerts.append("لا توجد عقبات كبيرة تُذكر. استمر في هذا الأداء الرائع! 💯")
                
            if not recommendations:
                positive_recommendations = [
                    "حافظ على وتيرة التعلم المنتظمة لتحقيق أقصى استفادة من إمكانياتك!",
                    "استمر في استكشاف مواضيع جديدة لتوسيع آفاق معرفتك!",
                    "التوازن بين المراجعة والتعلم الجديد هو مفتاح النجاح المستدام!"
                ]
                recommendations.append(random.choice(positive_recommendations))

        except Exception as e:
            print(f"Erreur génération messages: {e}")
            achievements.append("رحلة التعلم مليئة بالمفاجآت الجميلة. طفلك يحرز تقدماً كل يوم! 🌈")

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

