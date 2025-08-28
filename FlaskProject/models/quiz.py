from mongoengine import (
    Document,
    EmbeddedDocument,
    StringField,
    BooleanField,
    ListField,
    EmbeddedDocumentField,
    IntField,
    DateTimeField,
    signals,
)
import datetime


class Suggestion(EmbeddedDocument):
    txt = StringField()
    is_right = BooleanField()
    img_url = StringField()
    snd_url = StringField()


class Question(EmbeddedDocument):
    question_type = ListField(StringField())
    txt = StringField()
    img_url = StringField()
    snd_url = StringField()
    quiz_type = StringField()
    quiz_form = StringField()
    suggs_type = ListField(StringField())
    hint = StringField()
    suggestions = ListField(EmbeddedDocumentField(Suggestion))
    open = BooleanField()


class Layer(EmbeddedDocument):
    name = StringField()


class Quiz(Document):
    key = StringField(required=True, unique=True)
    teacherID = StringField()
    title = StringField()
    version = IntField()
    studio_version = IntField()
    game = StringField()
    time = IntField()
    level = StringField()
    # new fields: chapter, subject, grade
    subject = StringField()
    chapter = StringField()
    grade = StringField()
    language = StringField()
    tags = ListField(StringField())
    layers = ListField(EmbeddedDocumentField(Layer))
    questions = ListField(EmbeddedDocumentField(Question))
    status = StringField()

    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'quizesdata',
        'indexes': ['key'],
        'ordering': ['-created_at'],
    }

    # Pour gérer automatiquement updated_at à chaque sauvegarde
    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        document.updated_at = datetime.datetime.utcnow()


signals.pre_save.connect(Quiz.pre_save, sender=Quiz)
