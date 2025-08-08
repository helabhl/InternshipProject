const express = require('express');
const router = express.Router();
const controller = require('../controllers/quizAttemptsController');

// CRUD routes
router.post('/', controller.createQuizAttempt);
router.get('/', controller.getAllQuizAttempts);
router.get('/:userID/:kidIndex', controller.getAttemptsBykid);
router.get('/:userID/:kidIndex/:week', controller.getAttemptsByWeek);
router.post('/bulk', controller.bulkInsertQuizAttempts);


module.exports = router;
