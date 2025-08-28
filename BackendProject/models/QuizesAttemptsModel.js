const mongoose = require("mongoose");
require("dotenv").config();


const QuizesAttemptSchema = new mongoose.Schema({
  userID: {
    type: String, // 👈 userID, pas ObjectId
    required: true
  },
  kidIndex: {
    type: String, // 👈 clé de l’enfant dans "kids"
    required: true
  },
  quizID: {
    type: mongoose.Schema.Types.ObjectId, ref: 'quizes', required: true
  },
  start_time: { type: Date, required: true },
  end_time: { type: Date, required: true },
  q_i: [{ type: Number, required: true }],       // tableau 0/1 par question
  qi_hint: [{ type: Number, required: true }],   // nombre d’indices utilisés par question
  qi_wrong: [{ type: Number, required: true }],  // nombre de mauvaises tentatives par question
  score: { type: Number },
  completed: { type: Number },
  failed: { type: Number },
  abandoned: { type: Number },
}, { timestamps: true });

module.exports = mongoose.model('quizesattempts', QuizesAttemptSchema);
