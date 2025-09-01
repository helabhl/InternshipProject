# attempt.py
from mongoengine import *
from bson import ObjectId
from datetime import datetime, timezone

# =========================
# Tentative sur UNE question
# =========================
class QuestionAttempt(EmbeddedDocument):
    is_correct = IntField(min_value=0, required=True, default=0)   # 0 ou 1
    is_wrong = IntField(min_value=0, required=True, default=0)
    hint_used = IntField(min_value=0, required=True, default=0)

    # Temps
    start_time = DateTimeField()
    end_time = DateTimeField()
    duration = IntField(min_value=0, default=0)

    # Métadonnées
    response_value = StringField()
    # Facultatif (utile pour analyse)
    auto_corrected = BooleanField(default=False)                      # si une correction auto a été appliquée

    
# =========================
# Réponse à une question (global pour la question)
# =========================

class Answer(EmbeddedDocument):
    # Liste des tentatives faites sur cette question
    attempts = ListField(EmbeddedDocumentField(QuestionAttempt))
    
    # Performance brute
    correct_answer = IntField(min_value=0, required=True, default=0)  # nb de bonnes réponses (0/1 généralement)
    wrong_answer = IntField(min_value=0, required=True, default=0)    # nb de mauvaises réponses
    hint_used = IntField(min_value=0, required=True, default=0)       # nb d'indices utilisés

    # Temps de réponse
    start_time = DateTimeField()                                      # début de la question
    end_time = DateTimeField()                                        # fin de la question
    time_per_question = IntField(min_value=0, default=0)              # durée totale (s)


    # Métadonnées
    skipped = BooleanField(default=False)                             # question passée
    attempts_count = IntField(default=0)                              # nb de tentatives sur la question
    question_id = ObjectIdField()                                     # référence à la question (dans Quiz/Question)


class AttemptData(Document):
    # Contexte utilisateur
    userID = StringField(required=True)                               # ID parent/tuteur
    kidIndex = StringField(required=True)                             # index ou identifiant de l’enfant
    quizID = ObjectIdField(required=True)                             # référence au quiz

    # Global timing
    start_time = DateTimeField()                                      # début du quiz
    end_time = DateTimeField()                                        # fin du quiz
    duration = IntField(min_value=0, default=0)                       # durée totale (s)

    # Réponses
    answers = ListField(EmbeddedDocumentField(Answer))                # liste des réponses

    # Statistiques
    total_attempts = IntField(default=0)                              # nb de tentatives 
    answered_questions = IntField(default=0)
    score = FloatField(default=0.0)                                   # score global
    success_rate = FloatField(default=0.0)                            # ratio de réussite pondéré

    failed = IntField(default=0)                                      
    completed = IntField(default=0)                                  
    aborted = IntField(default=0) 
    timeout = IntField(default=0) 

    aborted_reason = StringField(choices=("closed_app", "quit_button", "lost_connection"), null=True)
    timeout_reason = StringField(choices=("inactivity", "cron", "session_expired"), null=True)

    # Appareil
    deviceType = StringField()                                        # mobile / desktop / tablet
    device = StringField()                                            # OS ou modèle

    # Tracking avancé
    session_id = StringField()                                        # id unique de session

    # Audit
    created_at = DateTimeField(default=datetime.now(timezone.utc))
    updated_at = DateTimeField(default=datetime.now(timezone.utc))

    meta = {
        'collection': 'attemptsdata',
        'ordering': ['-start_time'],
        'indexes': ['userID', 'kidIndex', 'quizID']
    }

    def init_answers(self, num_questions):
        """Initialise les réponses avec des valeurs par défaut"""
        self.answers = [Answer() for _ in range(num_questions)]
        self.total_questions = num_questions
