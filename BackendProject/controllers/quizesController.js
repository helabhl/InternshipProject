const Quiz = require('../models/QuizesModel');


exports.createQuiz  = async (req, res) => {
  try {
    const quizData = req.body;
    // Création et sauvegarde
    const quiz = new Quiz(quizData);
    await quiz.save();

    res.status(201).json({ message: 'Quiz créé avec succès', quiz_id: quiz._id });
  } catch (err) {
    console.error(err);
    if (err.code === 11000) { // clé unique en doublon
      return res.status(400).json({ error: 'Key quiz déjà utilisée' });
    }
    res.status(500).json({ error: 'Erreur serveur lors de la création du quiz' });
  }
};

exports.deleteQuiz = async (req, res) => {
  try {
    const { id } = req.params;
    const quiz = await Quiz.findByIdAndDelete(id);
    if (!quiz) {
      return res.status(404).json({ error: 'Quiz introuvable' });
    }
    res.json({ message: 'Quiz supprimé avec succès' });
  } catch (err) {
    res.status(500).json({ error: 'Erreur serveur lors de la suppression du quiz' });
  }
};

exports.getAllQuiz = async (req, res) => {
  try {
    const quizzes = await Quiz.find();
    res.json(quizzes);
  } catch (err) {
    res.status(500).json({ error: 'Erreur serveur lors de la récupération des quiz' });
  }
};

exports.getAllQuizByChapter = async (req, res) => {
  try {
    const { level, chapter } = req.query;
    const filter = {};
    if (level) filter.level = level;
    if (chapter) filter.chapter = chapter;

    const quizzes = await Quiz.find(filter).lean();
    res.json(quizzes);
  } catch (err) {
    res.status(500).json({ error: 'Erreur serveur lors de la récupération des quiz' });
  }
};

// GET /quizzes/subject/:subjectName
exports.getQuizzesBySubject = async (req, res) => {
  try {
    const subject = req.params.subjectName;

    const quizzes = await Quiz.find({ "layers.name": subject });

    res.json(quizzes);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Erreur serveur lors de la récupération des quiz' });
  }
};

exports.getQuizzesByFilters = async (req, res) => {
  try {
    const { subject, level, chapter } = req.query;
    let filter = {};

    if (subject) filter["layers.name"] = subject;
    if (level) filter.level = level;
    if (chapter) filter["layers.name"] = chapter; // si chapter est aussi dans layers

    const quizzes = await Quiz.find(filter);

    res.status(200).json(quizzes);
  } catch (err) {
    console.error("Erreur getQuizzesByFilters:", err);
    res.status(500).json({ error: "Erreur serveur lors du filtrage des quiz" });
  }
};
