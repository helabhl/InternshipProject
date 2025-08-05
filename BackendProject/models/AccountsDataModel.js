const mongoose = require("mongoose");
require("dotenv").config();

// Define the question attempt schema
const QuestionAttemptSchema = new mongoose.Schema(
  {
    hintUsed: { type: Boolean },
    isCorrect: { type: Boolean },
    isMobile: { type: Boolean },
    timeSpent: { type: Number },
    timestamp: { type: String },
  },
  { _id: false }
);

// Define the question schema
const QuestionSchema = new mongoose.Schema(
  {
    questionHintUsedCount: { type: Number, default: 0 },
    questionIndex: { type: Number },
    questionType: { type: [String] },
    quizForm: { type: String, default: "" },
    quizType: { type: String },
    attempts: { type: [QuestionAttemptSchema], default: [] },
  },
  { _id: false }
);

const QuizAttemptSchema = new mongoose.Schema(
  {
    completed: { type: Boolean },
    endTime: { type: String, default: "" },
    numOfQuestions: { type: Number },
    questions: { type: [QuestionSchema] },
    quiz_id: { type: String },
    score: { type: Number, default: 0 },
    startTime: { type: String },
    totalAttempts: { type: Number, default: 0 },
    totalHintsUsed: { type: Number, default: 0 },
    totalMistakes: { type: Number, default: 0 },
    totalTimeSpent: { type: Number, default: 0 },
  },
  { _id: false }
);

const QuizSchema = new mongoose.Schema(
  {
    TotalGlobalCompletion: { type: Number, default: 0 },
    quizesGLobalAttemps: { type: [QuizAttemptSchema], default: [] },
    totalFinishedGlobalHintsUsed: { type: Number, default: 0 },
    totalFinishedGlobalMistakes: { type: Number, default: 0 },
    totalFinishedQuizesGlobalAttempts: { type: Number, default: 0 },
    totalFinishedQuizesGlobalTimeSpent: { type: Number, default: 0 },
    totalFinishedQuizesGlobalscore: { type: Number, default: 0 },
    totalGlobalAttempts: { type: Number, default: 0 },
    totalGlobalHintsUsed: { type: Number, default: 0 },
    totalGlobalMistakes: { type: Number, default: 0 },
    totalGlobalTimeSpent: { type: Number, default: 0 },
  },
  { _id: false }
);

const UserSchema = new mongoose.Schema({
  achivementsUnlocked: { type: String },
  birthDate: { type: String },
  next_reward: { type: String },
  dictionnaryWordsUnlocked: { type: String },
  downBodyAccessoriesOwned: { type: String },
  downBodyAccessoriesWeared: { type: Number },
  gender: { type: String },
  keysUnlocked: { type: String },
  levelReached: { type: String },
  name: { type: String },
  starsCollected: { type: Number },
  surname: { type: String },
  upperBodyAccessoriesOwned: { type: String },
  upperBodyAccessoriesWeared: { type: Number },
  surveys: {
    type: Map,
    of: [String],
  },
  quizes: {
    type: Map,
    of: QuizSchema,
    default: {},
  },
});

const ActiveSessionsSchema = new mongoose.Schema(
  {
    Phone: {
      type: Map,
      of: String,
      default: {},
    },
    Web: {
      type: Map,
      of: String,
      default: {},
    },
  },
  { _id: false }
);

const AccountsDataSchema = new mongoose.Schema(
  {
    userID: { type: String, required: true },
    kids: {
      type: Map,
      of: UserSchema,
      default: {},
    },
    Active_Sessions: {
      type: ActiveSessionsSchema,
      default: () => ({ Phone: {}, Web: {} }),
    },
    authenticationType: { type: String },
    isPremium: { type: String },
    isTrialOoredooAvailable: { type: Boolean },
    memberShipCreationDate: { type: String },
    parentDate: { type: String },
    parentGender: { type: String },
    parentName: { type: String },
    subIdEklectic: { type: String },
    childNumber: { type: Number },
    maxChildren: { type: Number },
    maxChildren: { type: Number },
  },
  { timestamps: true }
);

module.exports = mongoose.model("accountsdatas", AccountsDataSchema);
