from flask import Blueprint
from controllers.performanceController import PerformanceController

performance_bp = Blueprint("performance", __name__)

@performance_bp.route("/user/<userId>/kid/<kidIndex>/messages-codes", methods=["GET"])
def messages_codes(userId, kidIndex):
    return PerformanceController.get_messages_codes(userId, kidIndex)

@performance_bp.route("/user/<userId>/kid/<kidIndex>/metrics", methods=["GET"])
def metrics(userId, kidIndex):
    return PerformanceController.get_metrics(userId, kidIndex)

@performance_bp.route("/user/<userId>/kid/<kidIndex>/performances", methods=["GET"])
def performances(userId, kidIndex):
    return PerformanceController.get_performance(userId, kidIndex)

@performance_bp.route("/user/<userId>/kid/<kidIndex>/weekly-scores", methods=["GET"])
def weekly_scores(userId, kidIndex):
    return PerformanceController.get_weekly_average_scores(userId, kidIndex)

@performance_bp.route("/user/<userId>/kid/<kidIndex>/subject-distribution", methods=["GET"])
def subject_distribution(userId, kidIndex):
    return PerformanceController.get_subject_distribution(userId, kidIndex)