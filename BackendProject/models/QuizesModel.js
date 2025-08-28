const mongoose = require('mongoose');

const suggestionSchema = new mongoose.Schema({
  txt: String,
  is_right: Boolean,
  img_url: String,
  snd_url: String,
});

const questionSchema = new mongoose.Schema({
  question_type: [String],
  txt: String,
  img_url: String,
  snd_url: String,
  quiz_type: String,
  quiz_form: String,
  suggs_type: [String],
  hint: String,
  suggestions: [suggestionSchema],
  open: Boolean,
});

const layerSchema = new mongoose.Schema({
  name: String,
});

const quizSchema = new mongoose.Schema({
  key: { type: String, required: true, unique: true },
  teacherID: String,
  title: String,
  version: Number,
  studio_version: Number,
  game: String,
  time: Number,
  level: String,
  language: String,
  tags: [String],
  layers: [layerSchema],
  questions: [questionSchema],
  status: String,
}, { timestamps: true });

const Quiz = mongoose.model('quizes', quizSchema);

module.exports = Quiz;
