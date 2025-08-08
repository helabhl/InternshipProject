const express = require("express"); 
const router = express.Router();
const QuizAttempt = require("../models/QuizAttemptModel");
const AccountsData = require("../models/AccountsDataModel");

// ✅ Route GET avec paramètres dans l'URL
router.get("/:parentID/:kidIndex/:period", async (req, res) => {
  const { parentID, kidIndex, period } = req.params;

  try {
    // ✅ Vérifier existence du parent
    const parentData = await AccountsData.findOne({ userID: parentID });
    if (!parentData) return res.status(404).json({ error: "Parent not found" });

    // ✅ Vérifier existence de l'enfant
    const childData = parentData.kids.get(kidIndex);
    if (!childData) return res.status(404).json({ error: "Child not found" });

    // ✅ Récupérer les quizAttempts du parent pour l'enfant
    const quizAttempts = await QuizAttempt.find({
      userID: parentID,
      kidIndex: kidIndex.toString()
    });

    // ✅ Fonction pour extraire la semaine ISO
    const getISOWeek = (date) => {
      const tmp = new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
      const day = tmp.getUTCDay() || 7;
      tmp.setUTCDate(tmp.getUTCDate() + 4 - day);
      const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1));
      const weekNo = Math.ceil((((tmp - yearStart) / 86400000) + 1) / 7);
      return `${tmp.getUTCFullYear()}-W${String(weekNo).padStart(2, '0')}`;
    };

    // 🔁 Regrouper par semaine ISO
    const weeklyMap = {};
    quizAttempts.forEach(attempt => {
      const isoWeek = getISOWeek(new Date(attempt.startTime));
      if (!weeklyMap[isoWeek]) weeklyMap[isoWeek] = [];
      weeklyMap[isoWeek].push(attempt);
    });

    // ✅ Filtrage selon la période
    let filtered = [];
    if (period === "weekly") {
      const sortedWeeks = Object.keys(weeklyMap).sort().reverse(); // ["2025-W34", "2025-W33", ...]
      const latestWeek = sortedWeeks[0];
      filtered = weeklyMap[latestWeek] || [];
    } else {
      filtered = quizAttempts;
    }

    if (filtered.length === 0) {
      return res.json({ message: "No quiz attempts found for this period." });
    }

    // ✅ Retourner les tentatives telles quelles (sans changement de modèle)
    res.json({ attempts: filtered });

  } catch (err) {
    console.error("Dashboard route error:", err);
    res.status(500).json({ error: "Server error" });
  }
});

module.exports = router;
