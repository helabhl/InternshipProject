const express = require('express');
const router = express.Router();
const quizAttemptsController = require('../controllers/quizAttemptsController');

// CRUD routes
router.post('/', quizAttemptsController.createQuizAttempt);
router.get('/', quizAttemptsController.getAllQuizAttempts);
router.get('/:id', quizAttemptsController.getQuizAttemptById);
router.put('/:id', quizAttemptsController.updateQuizAttempt);
router.delete('/:id', quizAttemptsController.deleteQuizAttempt);

module.exports = router;
