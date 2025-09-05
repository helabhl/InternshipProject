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
from datetime import datetime, timezone


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
    key = StringField(required=True)
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

    # Audit
    __v = IntField(default=0, db_field="__v")  # équivalent de versionKey
    createdAt = DateTimeField(default=datetime.now(timezone.utc))
    updatedAt = DateTimeField(default=datetime.now(timezone.utc))


    meta = {
        'collection': 'quizesdata',
        'indexes': ['key'],
        'ordering': ['-createdAt'],
        "strict": False  # ✅ ignore les champs inconnus comme __v

    }

    def save(self, *args, **kwargs):
        """Override save to auto-update updatedAt + increment __v"""
        if not self.createdAt:
            self.createdAt = datetime.now(timezone.utc)

        self.updatedAt = datetime.now(timezone.utc)

        self.__v = (self.__v or 0) + 1  # incrémentation automatique
        return super(Quiz, self).save(*args, **kwargs)

