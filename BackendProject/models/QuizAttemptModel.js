const mongoose = require("mongoose");
require("dotenv").config();


const QuizAttemptSchema = new mongoose.Schema({
  userID: {
    type: String, // 👈 userID, pas ObjectId
    required: true
  },
  kidIndex: {
    type: String, // 👈 clé de l’enfant dans "kids"
    required: true
  },
  quizID: {
    type: String, 
    required: true
  },
  subject: String,
  chapter: String,
  numOfQuizes: Number,
  numOfQuestions: Number,
  startTime: Date,
  duration: Number,
  score: Number,
  completed: Number,
  failed: Number,
  abandoned: Number,
}, { timestamps: true });

module.exports = mongoose.model('quizattempts', QuizAttemptSchema);
