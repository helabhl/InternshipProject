from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from controllers.attemptController import (
    create_attempt, update_attempt, abandon_attempt,
    recalculate_scores, get_all_attempts, get_attempt_by_id,
    get_attempts_per_kid, get_attempts_per_week, get_attempts_per_month
)

attempts_bp = Blueprint("attemptsdata", __name__)


@attempts_bp.route("/create-attempt", methods=["POST"])
def create_attempt_route():
    data = request.get_json()
    response, status = create_attempt(data)
    return jsonify(response), status


@attempts_bp.route("/update-attempt", methods=["POST"])
def update_attempt_route():
    data = request.get_json()
    response, status = update_attempt(data)
    return jsonify(response), status


@attempts_bp.route("/attempts/abandon", methods=["POST"])
def abandon_attempt_route():
    data = request.get_json()
    response, status = abandon_attempt(data)
    return jsonify(response), status


@attempts_bp.route("/attempts/recalculate_scores", methods=["POST"])
def recalculate_scores_route():
    response, status = recalculate_scores()
    return jsonify(response), status


@attempts_bp.route("/attempts", methods=["GET"])
def get_all_attempts_route():
    response, status = get_all_attempts()
    return jsonify(response), status


@attempts_bp.route("/attempts/<attempt_id>", methods=["GET"])
def get_attempt_by_id_route(attempt_id):
    response, status = get_attempt_by_id(attempt_id)
    return jsonify(response), status


@attempts_bp.route("/attempts/<user_id>/<kid_index>", methods=["GET"])
def get_attempts_per_kid_route(user_id, kid_index):
    from_str = request.args.get("from")
    to_str = request.args.get("to")
    to_date = datetime.now(timezone.utc) if not to_str else datetime.fromisoformat(to_str)
    from_date = to_date - timedelta(days=7) if not from_str else datetime.fromisoformat(from_str)

    response, status = get_attempts_per_kid(user_id, kid_index, from_date, to_date)
    return jsonify(response), status


@attempts_bp.route("/attempts/<user_id>/<kid_index>/week/<week_str>", methods=["GET"])
def get_attempts_per_week_route(user_id, kid_index, week_str):
    year, week_num = map(int, week_str.split("-W"))
    start_date = datetime.fromisocalendar(year, week_num, 1).replace(tzinfo=timezone.utc)
    end_date = (datetime.fromisocalendar(year, week_num, 7) + timedelta(days=1)).replace(tzinfo=timezone.utc)

    response, status = get_attempts_per_week(user_id, kid_index, start_date, end_date)
    return jsonify(response), status


@attempts_bp.route("/attempts/<user_id>/<kid_index>/month/<month_str>", methods=["GET"])
def get_attempts_per_month_route(user_id, kid_index, month_str):
    year, month = map(int, month_str.split("-"))
    if not (1 <= month <= 12):
        return jsonify({"error": "Mois invalide"}), 400

    start_date = datetime(year, month, 1, tzinfo=timezone.utc)
    if month == 12:
        end_date = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end_date = datetime(year, month + 1, 1, tzinfo=timezone.utc)

    response, status = get_attempts_per_month(user_id, kid_index, start_date, end_date)
    return jsonify(response), status
