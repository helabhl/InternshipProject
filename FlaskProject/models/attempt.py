from mongoengine import *
from bson import ObjectId
from datetime import datetime

class Answer(EmbeddedDocument):
    correct_answer = IntField(min_value=0, required=True, default=0)
    wrong_answer = IntField(min_value=0, required=True, default=0)
    hint_used = IntField(min_value=0, required=True, default=0)
    time_per_question = IntField(min_value=0,  default=0)
    start_time = DateTimeField()
    end_time = DateTimeField()



class AttemptData(Document):
    userID = StringField(required=True)
    kidIndex = StringField(required=True)
    quizID = ObjectIdField(required=True)
    start_time = DateTimeField()
    end_time = DateTimeField()
    answers = ListField(EmbeddedDocumentField(Answer))
    score = FloatField(default=0.0)
    failed = IntField(default=0)
    completed = IntField(default=0)
    abandoned = IntField(default=0)
    deviceType = StringField()
    device = StringField()

    meta = {
        'collection': 'attemptsdata',
        'ordering': ['-start_time'],
        'indexes': ['userID', 'kidIndex', 'quizID']
    }

    def init_answers(self, num_questions):
        self.answers = [Answer() for _ in range(num_questions)]
