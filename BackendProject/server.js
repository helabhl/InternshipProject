const express = require('express');
const mongoose = require('./db'); // ou require('./db.js')

const AccountData = require('./models/AccountsDataModel'); // ton modèle mongoose
const QuizAttempt = require('./models/QuizAttemptModel');


const app = express();
app.use(express.json());

const PORT = process.env.PORT || 3000;

app.get('/', async (req, res) => {
  // Récupérer page et limit depuis la query string, ex: /?page=2&limit=5
  let { page = 1, limit = 5 } = req.query;

  // Convertir en nombre
  page = parseInt(page);
  limit = parseInt(limit);

  try {
    console.log(`🔍 Récupération des comptes page ${page} avec limite ${limit}`);
    const accounts = await AccountData.find({})
      .skip((page - 1) * limit)
      .limit(limit);
    res.json(accounts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const quizAttemptsRoutes = require('./routes/quizAttemptsRoutes');
app.use('/quiz-attempts', quizAttemptsRoutes);


app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
