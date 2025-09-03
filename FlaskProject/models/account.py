from mongoengine import *
import config

# Connexion MongoDB (à mettre dans ton app Flask)
connect(config.DB_NAME, host=config.MONGO_URI)

# --- Sous-schemas ---

class QuestionAttempt(EmbeddedDocument):
    hintUsed = BooleanField()
    isCorrect = BooleanField()
    isMobile = BooleanField()
    timeSpent = IntField()
    timestamp = StringField()

class Question(EmbeddedDocument):
    questionHintUsedCount = IntField(default=0)
    questionIndex = IntField()
    questionType = ListField(StringField())
    quizForm = StringField(default="")
    quizType = StringField()
    attempts = EmbeddedDocumentListField(QuestionAttempt, default=[])

class QuizAttempt(EmbeddedDocument):
    completed = BooleanField()
    endTime = StringField(default="")
    numOfQuestions = IntField()
    questions = EmbeddedDocumentListField(Question)
    quiz_id = StringField()
    score = IntField(default=0)
    startTime = StringField()
    totalAttempts = IntField(default=0)
    totalHintsUsed = IntField(default=0)
    totalMistakes = IntField(default=0)
    totalTimeSpent = IntField(default=0)

class Quiz(EmbeddedDocument):
    TotalGlobalCompletion = IntField(default=0)
    quizesGLobalAttemps = EmbeddedDocumentListField(QuizAttempt, default=[])
    totalFinishedGlobalHintsUsed = IntField(default=0)
    totalFinishedGlobalMistakes = IntField(default=0)
    totalFinishedQuizesGlobalAttempts = IntField(default=0)
    totalFinishedQuizesGlobalTimeSpent = IntField(default=0)
    totalFinishedQuizesGlobalscore = IntField(default=0)
    totalGlobalAttempts = IntField(default=0)
    totalGlobalHintsUsed = IntField(default=0)
    totalGlobalMistakes = IntField(default=0)
    totalGlobalTimeSpent = IntField(default=0)

class ActiveSessions(EmbeddedDocument):
    Phone = MapField(StringField(), default={})
    Web = MapField(StringField(), default={})

class User(EmbeddedDocument):
    achivementsUnlocked = StringField()
    birthDate = StringField()
    next_reward = StringField()
    dictionnaryWordsUnlocked = StringField()
    downBodyAccessoriesOwned = StringField()
    downBodyAccessoriesWeared = IntField()
    gender = StringField()
    keysUnlocked = StringField()
    levelReached = StringField()
    name = StringField()
    starsCollected = IntField()
    surname = StringField()
    upperBodyAccessoriesOwned = StringField()
    upperBodyAccessoriesWeared = IntField()
    surveys = MapField(ListField(StringField()))
    quizes = MapField(EmbeddedDocumentField(Quiz), default={})

class AccountData(Document):
    userID = StringField(required=True, unique=True)
    # phone, email, mot de passe : new fields (, unique=True)
    # phone = StringField(required=True)
    # email = StringField(required=True)
    # password_hash = StringField(required=True)
    kids = MapField(EmbeddedDocumentField(User), default={})
    Active_Sessions = EmbeddedDocumentField(ActiveSessions, default=ActiveSessions)
    authenticationType = StringField()
    isPremium = StringField()
    isTrialOoredooAvailable = BooleanField()
    memberShipCreationDate = StringField()
    parentDate = StringField()
    parentGender = StringField()
    parentName = StringField()
    subIdEklectic = StringField()
    childNumber = IntField()
    maxChildren = IntField()

    meta = {
        'collection': 'accountsdatas',
        'ordering': ['-id']
    }
