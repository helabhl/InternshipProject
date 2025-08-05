const mongoose = require('mongoose');

const QuizAttemptSchema = new mongoose.Schema({
  child_id: { type: String},
  grade: { type: Number },
  subject: { type: String },
  chapter: { type: String },
  num_quizzes: { type: Number },
  quiz_id: { type: String },
  nb_questions: { type: Number },
  start_time: { type: Date },
  time_spent: { type: Number }, 
  attempts_count: { type: Number },
  prev_final_score: { type: Number },
  final_score: { type: Number },
  completed: { type: Boolean },
  failed: { type: Boolean },
  abandoned: { type: Boolean },
  correct_count: { type: Number },
  wrong_count: { type: Number },
  hint_count: { type: Number },
}, { timestamps: true });

module.exports = mongoose.model('quizattempts', QuizAttemptSchema);
