const express = require('express');
const mongoose = require('./db'); 

const AccountData = require('./models/AccountsDataModel'); 
const QuizAttempt = require('./models/QuizAttemptModel');


const app = express();
app.use(express.json());

const PORT = process.env.PORT;


const accountsRoutes = require('./routes/accountsDataRoutes');
app.use('/accounts', accountsRoutes);

const quizesRoutes = require('./routes/quizesRoutes');
app.use('/quizes', quizesRoutes);

const quizesAttemptsRoutes = require('./routes/quizesAttemptsRoutes');
app.use('/quiz-attempts', quizesAttemptsRoutes);

const attemptsRoutes = require('./routes/quizAttemptsRoutes');
app.use('/attempts', attemptsRoutes);


app.get('/', (req, res) => {
  res.send('Hello from root!');
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
