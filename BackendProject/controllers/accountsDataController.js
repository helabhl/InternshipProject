const AccountsData = require('../models/AccountsDataModel');

exports.createAccount = async (req, res) => {
  try {
    const account = new AccountsData(req.body);
    const savedAccount = await account.save();
    res.status(201).json(savedAccount);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
};

exports.getAllAccounts = async (req, res) => {
  try {
    const accounts = await AccountsData.find();
    res.json(accounts);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};
