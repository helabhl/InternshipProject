// controllers/quizAttemptsController.js
const QuizAttempt = require('../models/QuizAttemptModel'); // ajuste le chemin si besoin

// Create a new quiz attempt
exports.createQuizAttempt = async (req, res) => {
  console.log('📥 Données reçues dans le body :', req.body);
  try {
    const newAttempt = new QuizAttempt(req.body);
    const savedAttempt = await newAttempt.save();
    res.status(201).json(savedAttempt);
  } catch (err) {
    console.error('❌ Error creating attempt:', err);
    res.status(500).json({ error: err.message });
  }
};


// Get all quiz attempts (with optional pagination)
exports.getAllQuizAttempts = async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;

    const attempts = await QuizAttempt.find()
      .skip((page - 1) * limit)
      .limit(limit);

    res.json(attempts);
  } catch (err) {
    console.error('❌ Error fetching attempts:', err);
    res.status(500).json({ error: err.message });
  }
};

// Get a single quiz attempt by ID
exports.getQuizAttemptById = async (req, res) => {
  try {
    const attempt = await QuizAttempt.findById(req.params.id);
    if (!attempt) return res.status(404).json({ error: 'Not found' });
    res.json(attempt);
  } catch (err) {
    console.error('❌ Error fetching attempt:', err);
    res.status(500).json({ error: err.message });
  }
};

// Update a quiz attempt by ID
exports.updateQuizAttempt = async (req, res) => {
  try {
    const updatedAttempt = await QuizAttempt.findByIdAndUpdate(
      req.params.id,
      req.body,
      { new: true }
    );
    if (!updatedAttempt) return res.status(404).json({ error: 'Not found' });
    res.json(updatedAttempt);
  } catch (err) {
    console.error('❌ Error updating attempt:', err);
    res.status(500).json({ error: err.message });
  }
};

// Delete a quiz attempt by ID
exports.deleteQuizAttempt = async (req, res) => {
  try {
    const deleted = await QuizAttempt.findByIdAndDelete(req.params.id);
    if (!deleted) return res.status(404).json({ error: 'Not found' });
    res.json({ message: 'Deleted successfully' });
  } catch (err) {
    console.error('❌ Error deleting attempt:', err);
    res.status(500).json({ error: err.message });
  }
};
