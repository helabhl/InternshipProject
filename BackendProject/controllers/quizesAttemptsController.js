const QuizAttempt = require('../models/QuizesAttemptsModel');
const Quiz = require('../models/QuizesModel'); // pour valider quiz_id


function calculateScore(numOfQuestions, q_i, qi_hint, qi_wrong, timeSpent) {
  // Calcul du Success Rate par question i
  let sumSuccessRate = 0;
  for (let i = 0; i < numOfQuestions; i++) {
    const numerator = q_i[i];
    const denominator = qi_wrong[i] + qi_hint[i] + 1;
    sumSuccessRate += numerator / denominator;
  }
  const avgSuccessRate = sumSuccessRate / numOfQuestions;

  // Calcul de la vitesse (speed)
  const correctCount = q_i.reduce((acc, val) => acc + val, 0);
  let timePerQuestion = 0;
  if (correctCount > 0) {
    timePerQuestion = timeSpent / correctCount;
  }

  const minTime = 15;
  const maxTime = 360;
  let speed = 0;

  if (timePerQuestion < minTime) {
    speed = 1;
  } else if (timePerQuestion <= maxTime) {
    speed = 1 - (timePerQuestion - minTime) / (maxTime - minTime);
  } else {
    speed = 0;
  }

  const score = 0.8 * avgSuccessRate + 0.2 * speed;
  return score;
}

exports.createAttempt  =  async (req, res) => {
  try {
    const {  userID, kidIndex, quizID, start_time, end_time, q_i, qi_hint, qi_wrong } = req.body;

    // Validation minimale
    if (!quizID || !userID || kidIndex === undefined || !start_time || !end_time || !q_i || !qi_hint || !qi_wrong) {
      return res.status(400).json({ error: 'Champs manquants' });
    }
    if (!(q_i.length === qi_hint.length && qi_hint.length === qi_wrong.length)) {
      return res.status(400).json({ error: 'Les tableaux q_i, qi_hint, qi_wrong doivent avoir la même longueur' });
    }

    // Valider que le quiz existe
    const quiz = await Quiz.findById(quizID);
    if (!quiz) {
      return res.status(404).json({ error: 'Quiz non trouvé' });
    }

    const numOfQuestions = quiz.questions.length;
    if (q_i.length !== numOfQuestions) {
      return res.status(400).json({ error: 'La longueur de q_i ne correspond pas au nombre de questions du quiz' });
    }

    const startDate = new Date(start_time);
    const endDate = new Date(end_time);
    if (endDate <= startDate) {
      return res.status(400).json({ error: 'end_time doit être après start_time' });
    }

    const timeSpent = (endDate - startDate) / 1000; // en secondes

    // Calcul du score
    const score = calculateScore(numOfQuestions, q_i, qi_hint, qi_wrong, timeSpent);
    // Calcul correct_answers
    const correct_answers = q_i.reduce((acc, val) => acc + val, 0);

    // Calcul total_wrong_attempts (total erreurs sur toutes questions)
    const total_wrong_attempts = qi_wrong.reduce((acc, val) => acc + val, 0);


    // Calcul des flags
    const completed = correct_answers === numOfQuestions ? 1 : 0;
    const failed = (total_wrong_attempts >= 3 && correct_answers < numOfQuestions) ? 1 : 0;
    const abandoned = (total_wrong_attempts < 3 && correct_answers < numOfQuestions) ? 1 : 0;

    // Création et sauvegarde de la tentative
    const attempt = new QuizAttempt({
      userID,
      kidIndex,
      quizID,
      start_time: startDate,
      end_time: endDate,
      q_i,
      qi_hint,
      qi_wrong,
      score,
      completed,
      failed,
      abandoned
    });

    await attempt.save();

    res.status(201).json({ message: 'Tentative enregistrée', score, attempt_id: attempt._id });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Erreur serveur' });
  }
};
exports.getAttemptsperkid = async (req, res) => {
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

exports.getAttemptsByPeriod = async (req, res) => {
  try {
    const { userID, kidIndex, week } = req.params; // ex : "2025-W32"

    const startDate = moment(week, "GGGG-[W]WW").startOf('isoWeek').toDate();
    const endDate = moment(week, "GGGG-[W]WW").endOf('isoWeek').toDate();

    // Filtrage avec jointure
    const attempts = await QuizAttempt.find({
      userID,
      kidIndex,
      start_time: { $gte: startDate, $lte: endDate },
    })
    .populate({
      path: "quizID",
      select: "layers",
    })
    .lean(); // lean() = objets JS simples

    // Transformer pour extraire level, subject, chapter
    const formattedAttempts = attempts.map(attempt => {
      const layers = attempt.quizID?.layers || [];
      return {
        ...attempt,
        level: layers[0]?.name || null,
        subject: layers[1]?.name || null,
        chapter: layers[2]?.name || null,
      };
    });

    res.status(200).json(formattedAttempts);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};

