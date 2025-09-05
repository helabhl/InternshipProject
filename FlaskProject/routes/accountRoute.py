from flask import Blueprint, request, jsonify
from controllers.accountController import (
    create_account,
    get_all_accounts,
    get_account,
    get_kids,
    get_kids_names
)

accounts_bp = Blueprint("accountsdatas", __name__, url_prefix="/accounts")


@accounts_bp.route("/", methods=["POST"])
def create_account_route():
    data = request.get_json()
    response, status = create_account(data)
    return jsonify(response), status


@accounts_bp.route("/", methods=["GET"])
def get_all_accounts_route():
    response, status = get_all_accounts()
    return jsonify(response), status


@accounts_bp.route("/<user_id>", methods=["GET"])
def get_account_route(user_id):
    response, status = get_account(user_id)
    return jsonify(response), status


@accounts_bp.route("/<user_id>/kids", methods=["GET"])
def get_kids_route(user_id):
    response, status = get_kids(user_id)
    return jsonify(response), status


@accounts_bp.route("/get_kids_names/<user_id>", methods=["GET"])
def get_kids_names_route(user_id):
    response, status = get_kids_names(user_id)
    return jsonify(response), status
