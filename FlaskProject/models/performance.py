from mongoengine import *
from datetime import datetime


# --- Détails par chapitre ---
class ChapterDetails(EmbeddedDocument):
    attempts = IntField(required=True, default=0)
    average_score = FloatField(required=True, default=0.0)


# --- Détails par matière ---
class SubjectStats(EmbeddedDocument):
    average_score = FloatField(required=True, default=0.0)
    completed = IntField(required=True, default=0)
    count = IntField(required=True, default=0)


# --- Persévérance ---
class Perseverance(EmbeddedDocument):
    improved = IntField(required=True, default=0)
    perseverance_score = IntField(required=True, default=0)
    retries = IntField(required=True, default=0)


# --- Modèle principal ---
class Metrics(Document):
    abandon_rate = ListField(IntField(), default=list)              # ex: [0, 2]
    chapter_distribution = MapField(EmbeddedDocumentField(ChapterDetails), default=dict)
    completion_rate = ListField(IntField(), default=list)           # ex: [1, 2]
    engagement = ListField(IntField(), default=list)                # ex: [2, 7]
    mastery = MapField(FloatField(), default=dict)                  # ex: {"رياضيات": 0.8}
    perseverance = EmbeddedDocumentField(Perseverance, default=Perseverance)
    persistent_failures = MapField(FloatField(), default=dict)      # ex: {"رياضيات": 0.3} (vide au départ)
    progress = FloatField(default=0.0)
    recommendation = StringField(default="")
    speed_improvement = FloatField(default=0.0)
    streak = IntField(default=0)
    subject_balance = IntField(default=0)                           # ex: 75
    subject_stats = MapField(EmbeddedDocumentField(SubjectStats), default=dict)
    time_spent = FloatField(default=0.0)                            # ex: 9.73

    created_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'metrics',
        'ordering': ['-created_at'],
        'indexes': []
    }
