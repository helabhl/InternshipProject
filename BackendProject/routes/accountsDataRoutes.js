const express = require('express');
const router = express.Router();
const controller = require('../controllers/accountsDataController');

router.post('/', controller.createAccount);
router.get('/', controller.getAllAccounts);
router.get('/:userID', controller.getAccountByUserID);
module.exports = router;
