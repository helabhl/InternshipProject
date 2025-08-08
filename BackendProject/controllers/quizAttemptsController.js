const QuizAttempt = require('../models/QuizAttemptModel');

exports.createQuizAttempt = async (req, res) => {
    try {
        const newAttempt = await QuizAttempt.create(req.body);
        res.status(201).json(newAttempt);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
};

exports.getAllQuizAttempts = async (req, res) => {
    try {
        const attempts = await QuizAttempt.find({});
        res.json(attempts);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
};

exports.getAttemptsBykid = async (req, res) => {
    try {
    const { userID, kidIndex } = req.params;

    const attempts = await QuizAttempt.find({
      userID,
      kidIndex,
    });

    res.status(200).json(attempts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

const moment = require('moment'); // npm install moment

exports.getAttemptsByWeek = async (req, res) => {
  try {
    const {userID, kidIndex, week } = req.params; // Format attendu : "2025-W32"

    // Calcul du début et fin de la semaine ISO à partir de "2025-W32"
    const startDate = moment(week).startOf('isoWeek').toDate(); // lundi
    const endDate = moment(week).endOf('isoWeek').toDate();     // dimanche

    // Filtrage
    const attempts = await QuizAttempt.find({
      userID,
      kidIndex,
      startTime: {
        $gte: startDate,
        $lte: endDate,
      },
    });

    res.status(200).json(attempts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};



// POST /attempts/bulk
exports.bulkInsertQuizAttempts = async (req, res) => {
  try {
    const newAttempts = await QuizAttempt.insertMany(req.body);
    res.status(201).json({ message: "Attempts inserted", data: newAttempts });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
};
