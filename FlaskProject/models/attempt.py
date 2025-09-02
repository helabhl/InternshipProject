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
    duration = IntField(min_value=0, default=0)              # durée totale (s)


    
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
    attempts_count = IntField(default=0)                              # nb de tentatives 
    answered_questions = IntField(default=0)
    success_rate = FloatField(default=0.0)                            # ratio de réussite pondéré
    score = FloatField(default=0.0)                                   # score global


    failed = IntField(default=0)                                      
    completed = IntField(default=0)                                  
    aborted = IntField(default=0) 
    timeout = IntField(default=0) 

    # Appareil
    deviceType = StringField()                                        # mobile / desktop / tablet
    device = StringField()                                            # OS ou modèle


    # Audit
    created_at = DateTimeField()  
    updated_at = DateTimeField()  

    meta = {
        'collection': 'attemptsdata',
        'ordering': ['-start_time'],
        'indexes': ['userID', 'kidIndex', 'quizID']
    }

    def init_answers(self, num_questions):
        """Initialise les réponses avec des valeurs par défaut"""
        self.answers = [Answer() for _ in range(num_questions)]
        self.total_questions = num_questions
