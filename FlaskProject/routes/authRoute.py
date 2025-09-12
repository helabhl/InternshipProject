from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
from controllers.authController import  login_sms_logic, verify_logic
from models.account import AccountData
from bson import ObjectId

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login_sms():
    if request.method == "POST":
        user_id = request.form.get("userID")
        response, status = login_sms_logic(user_id)

        if status != 200:
            flash(response["error"], "danger")
            return render_template("users/login.html")

        return redirect(url_for("auth.verify"))

    return render_template("users/login.html")



@auth_bp.route("/verify", methods=["GET", "POST"])
def verify():

    def convert_objectid(obj):
        """Convertit récursivement tous les ObjectId en str."""
        if isinstance(obj, dict):
            return {k: convert_objectid(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_objectid(i) for i in obj]
        elif isinstance(obj, ObjectId):
            return str(obj)
        else:
            return obj

    if request.method == "POST":

        entered_code = request.form.get("otp")
        response, status = verify_logic(entered_code)

        if status == 200:
            account_dict = convert_objectid(response["account"])
            # Stocker dans la session
            session['account'] = account_dict
            return redirect(url_for("accountsdatas.dashboard"))
        else:
            flash(response["error"], "danger")

    return render_template("users/verify.html")


@auth_bp.route("/auth/dashboard/<userID>/<kidIndex>", methods=["GET"])
def get_dashboard(userID, kidIndex): 
    if not userID: 
        return "userID is required", 400 
    account = AccountData.objects(userID=userID).first() 
    if not account: 
        return "User not found", 404 
    # On passe l'objet account au template dashboard.html 
    return render_template("users/dashboard.html", parent=account, kid=kidIndex)
   