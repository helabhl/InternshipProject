from flask import Blueprint, request, session, flash, redirect, url_for, render_template
from models.account import AccountData
from twilio.rest import Client
from werkzeug.security import check_password_hash
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Twilio credentials
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
VERIFY_SERVICE_SID = os.getenv("VERIFY_SERVICE_SID")  
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login_sms', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('userID')
        if not user_id:
            flash("Please enter your UserID", "danger")
            return render_template("users/login_sms.html")

        # Search in MongoDB
        account = AccountData.objects(userID=user_id).first()
        if not account:
            flash("UserID not found", "danger")
            return render_template("users/login_sms.html")

        # Get phone from account
        phone = getattr(account, "phone", None)  # adapt if stored differently
        if not phone:
            flash("Phone number not found for this user", "danger")
            return render_template("users/login_sms.html")

        # Save user_id in session for verification step
        session['user_id'] = user_id
        session['phone'] = phone

        try:
            # Send OTP via Twilio Verify
            verification = client.verify.v2.services(VERIFY_SERVICE_SID) \
                .verifications \
                .create(to=phone, channel="sms")

            return redirect(url_for('auth.verify'))
        except Exception as e:
            flash(f"Error sending OTP: {str(e)}", "danger")

    return render_template("users/login_sms.html")


@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        code = request.form.get('otp')
        phone = session.get('phone')
        user_id = session.get('user_id')

        if not phone or not user_id:
            flash("Session expired, please login again", "danger")
            return redirect(url_for('auth.login'))

        try:
            # Check OTP via Twilio Verify
            verification_check = client.verify.v2.services(VERIFY_SERVICE_SID) \
                .verification_checks \
                .create(to=phone, code=code)

            if verification_check.status == "approved":
                account = AccountData.objects(userID=user_id).first()
                return render_template("users/dashboard.html", parent=account)
            else:
                flash("Invalid code", "danger")
        except Exception as e:
            flash(f"Error verifying code: {str(e)}", "danger")

    return render_template("users/verify.html")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login_account():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Please enter both email and password", "danger")
            return render_template("users/login.html")

        # Chercher l'utilisateur dans AccountData
        account = AccountData.objects(email=email).first()
        if not account:
            flash("No account found with this email", "danger")
            return render_template("users/login.html")

        # Vérifier le mot de passe
        if not check_password_hash(account.password_hash, password):
            flash("Incorrect password", "danger")
            return render_template("users/login.html")

        # Connexion réussie
        session['user_id'] = str(account.id)
        # return redirect(url_for('dashboard'))  # route à créer pour le tableau de bord
        return render_template("users/dashboard.html", parent=account)

    return render_template("users/login.html")

