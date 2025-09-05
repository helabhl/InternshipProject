from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
from controllers.authController import login_sms_logic, verify_logic
from models.account import AccountData

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login_sms", methods=["GET", "POST"])
def login_sms():
    if request.method == "POST":
        user_id = request.form.get("userID")
        response, status = login_sms_logic(user_id)

        if status != 200:
            flash(response["error"], "danger")
            return render_template("users/login_sms.html")

        return redirect(url_for("auth.verify"))

    return render_template("users/login_sms.html")


@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        entered_code = request.form.get("otp")
        response, status = verify_logic(entered_code)

        if status == 200:
            account_dict = response["account"]
            return render_template("users/home.html", parent=account_dict)
        else:
            flash(response["error"], "danger")

    return render_template("users/verify.html")
