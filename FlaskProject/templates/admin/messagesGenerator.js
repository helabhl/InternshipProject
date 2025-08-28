// messagesGenerator.js - Version Arabe
class ArabicMessagesGenerator {
  constructor() {
    this.language = 'ar';
    this.messages = this.arabicMessages();
  }

  arabicMessages() {
    return {
      engagement: {
        high: (days, total) => `🔥 تفانٍ استثنائي! ${days} أيام من الممارسة هذا الأسبوع!`,
        medium: (days, total) => `🌟 انتظام جيد! ${days} أيام من ${total}!`,
        low: (days, total) => `🌱 بداية عادة! ${days} يوم(أيام) ممارسة هذا الأسبوع.`
      },

      performance: {
        excellent: (high, total) => `🎯 إتقان مذهل! ${high}/${total} اختبار بنسبة أكثر من 80%!`,
        good: (high, total) => `👍 أداء ممتاز! ${high} اختبار ناجح جداً!`,
        average: (high, total) => `✨ ${high} نجاح(نجاحات) رائعة هذا الأسبوع!`
      },

      streak: {
        amazing: (streak) => `🚀 سلسلة مذهلة! ${streak} اختبارات ناجحة متتالية!`,
        great: (streak) => `🔥 في تدفق كامل! ${streak} نجاحات متتالية!`
      },

      completion: {
        perfect: (completed, started) => `💯 مثابرة! ${completed} اختبار مكتمل من ${started} بدأ!`,
        good: (completed, started) => `📚 معدل إكمال جيد: ${Math.round((completed/started)*100)}% من الاختبارات منتهية!`,
        average: (completed, started) => `✊ استمر هكذا! ${completed} اختبار مكتمل هذا الأسبوع.`
      },

      progress: {
        amazing: (progress) => `📈 تقدم صاروخي! +${Math.round(progress*100)}% من النقاط في أسبوعين!`,
        good: (progress) => `↗️ في تحسن ملحوظ! +${Math.round(progress*100)}% تقدم`,
        average: (progress) => `🌱 تحسن طفيف في النقاط (+${Math.round(progress*100)}%)`
      },

      mastery: {
        multiple: (subjects) => `🏆 خبير متعدد المواد: إتقان تام في ${subjects}!`,
        single: (subject, score) => `👑 إتقان ممتاز في ${subject} (${Math.round(score*100)}%)!`
      },

      speed: {
        amazing: (improvement) => `⚡ سرعة مضاعفة! ${Math.round(improvement*100)}% أسرع!`,
        good: (improvement) => `⏱️ وقت استجابة محسن بنسبة ${Math.round(improvement*100)}%`
      },

      records: {
        absolute: (score, subject) => `🚀 رقم قياسي مطلق! ${Math.round(score*100)}% في ${subject}!`,
        personal: (score, subject) => `✨ رقم شخصي متجاوز! ${Math.round(score*100)}% في ${subject}`
      },

      perseverance: {
        amazing: (count) => `🧠 تصميم لا يصدق! ${count} محاولات ناجحة!`,
        good: (count) => `💪 مثابرة مجزية! ${count} فشل(إخفاقات) تم التغلب عليها`
      },

      diversity: {
        perfect: (count) => `🌈 توازن مثالي! ${count}+ مواد مختلفة!`,
        good: (count) => `🌍 تنوع جيد: ${count} مواد تمت دراستها`
      }
    };
  }

  generateMessages(metrics) {
    const messages = [];
    const msg = this.messages;

    // 1. رسائل الالتزام
    if (metrics.engagement) {
      const { days, total_days } = metrics.engagement;
      if (days >= 5) messages.push(msg.engagement.high(days, total_days));
      else if (days >= 3) messages.push(msg.engagement.medium(days, total_days));
      else if (days > 0) messages.push(msg.engagement.low(days, total_days));
    }

    // 2. رسائل الأداء
    if (metrics.performance) {
      const { high_scores, total_completed } = metrics.performance;
      if (total_completed > 0) {
        const ratio = high_scores / total_completed;
        if (ratio >= 0.8) messages.push(msg.performance.excellent(high_scores, total_completed));
        else if (ratio >= 0.6) messages.push(msg.performance.good(high_scores, total_completed));
        else if (ratio > 0) messages.push(msg.performance.average(high_scores, total_completed));
      }
    }

    // 3. رسائل السلسلة
    if (metrics.streak >= 5) messages.push(msg.streak.amazing(metrics.streak));
    else if (metrics.streak >= 3) messages.push(msg.streak.great(metrics.streak));

    // 4. رسائل الإكمال
    if (metrics.completion_rate) {
      const { completed, started } = metrics.completion_rate;
      const rate = completed / started;
      if (rate >= 0.9) messages.push(msg.completion.perfect(completed, started));
      else if (rate >= 0.7) messages.push(msg.completion.good(completed, started));
      else if (completed > 0) messages.push(msg.completion.average(completed, started));
    }

    // ... استمرار لباقي الرسائل

    if (messages.length === 0) {
      messages.push("🌱 كل التقدم الكبير يبدأ صغيراً - استمر!");
    }

    return messages;
  }

  generateAlerts(metrics) {
    const alerts = [];

    // تنبيهات معدل التخلي
    if (metrics.abandon_rate > 0.5) {
      alerts.push({
        type: "high_abandon_rate",
        severity: "high",
        message: `⚠️ معدل تخلي مرتفع جداً: ${Math.round(metrics.abandon_rate*100)}%`,
        recommendation: "ناقش الصعوبات وشجع على المثابرة"
      });
    } else if (metrics.abandon_rate > 0.2) {
      alerts.push({
        type: "medium_abandon_rate",
        severity: "medium",
        message: `📉 ${Math.round(metrics.abandon_rate*100)}% من الاختبارات تم التخلي عنها`,
        recommendation: "تحقق من صعوبة وطول الوقت للاختبارات"
      });
    }

    // تنبيهات الإخفاق المستمر
    if (metrics.persistent_failures && metrics.persistent_failures.count >= 3) {
      alerts.push({
        type: "persistent_failure",
        severity: "high",
        message: `🚧 صعوبة مستمرة: ${metrics.persistent_failures.count} إخفاق في '${metrics.persistent_failures.quiz_name}'`,
        recommendation: "مراجعة المفاهيم الأساسية مطلوبة"
      });
    }

    // تنبيهات الدرجات المنخفضة
    if (metrics.performance && metrics.performance.average_score < 0.5) {
      alerts.push({
        type: "low_average_score",
        severity: "medium",
        message: `📊 متوسط درجات منخفض: ${Math.round(metrics.performance.average_score*100)}%`,
        recommendation: "تعزيز الأساسيات قبل المتابعة"
      });
    }

    // تنبيهات الوقت
    if (metrics.time_metrics && metrics.time_metrics.avg_time_per_attempt < 2) {
      alerts.push({
        type: "low_effort_time",
        severity: "medium",
        message: `⏱️ وقت متوسط قصير جداً: ${metrics.time_metrics.avg_time_per_attempt.toFixed(1)} دقيقة/اختبار`,
        recommendation: "شجع على التفكير المتعمق"
      });
    }

    // تنبيهات عدم النشاط
    if (metrics.engagement && metrics.engagement.recent_attempts === 0) {
      alerts.push({
        type: "no_recent_activity",
        severity: "low",
        message: "📅 لا يوجد نشاط هذا الأسبوع",
        recommendation: "خطط لجلسات مراجعة منتظمة"
      });
    }

    return alerts;
  }
}

// Hook React للغة العربية
export const useArabicKidMetrics = (userId, kidIndex) => {
  const [metrics, setMetrics] = useState(null);
  const [messages, setMessages] = useState([]);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`/metrics/${userId}/kids/${kidIndex}`);
        const metricsData = await response.json();
        
        setMetrics(metricsData);
        
        const generator = new ArabicMessagesGenerator();
        setMessages(generator.generateMessages(metricsData));
        setAlerts(generator.generateAlerts(metricsData));
        
      } catch (error) {
        console.error('خطأ في تحميل البيانات:', error);
      }
    };

    fetchData();
  }, [userId, kidIndex]);

  return { metrics, messages, alerts };
};