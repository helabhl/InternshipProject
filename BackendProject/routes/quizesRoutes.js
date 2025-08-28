const express = require('express');
const router = express.Router();
const controller = require('../controllers/quizesController');

// CRUD routes
router.post('/', controller.createQuiz);
router.delete('/:id', controller.deleteQuiz);
router.get('/', controller.getAllQuiz);
router.get('/filter', controller.getQuizzesByFilters);
router.get('/subject/:subject', controller.getQuizzesBySubject);


module.exports = router;