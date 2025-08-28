const express = require('express');
const router = express.Router();
const controller = require('../controllers/quizesAttemptsController');

// CRUD routes
router.post('/', controller.createAttempt);
router.get('/:userID/:kidIndex', controller.getAttemptsperkid);
router.get('/:userID/:kidIndex/:week', controller.getAttemptsByPeriod);

module.exports = router;