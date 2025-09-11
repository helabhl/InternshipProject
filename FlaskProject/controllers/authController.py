from flask import render_template, session
from models.account import AccountData


def login_sms_logic(user_id):
    if not user_id:
        return {"error": "Please enter your UserID"}, 400

    account = AccountData.objects(userID=user_id).first()
    if not account:
        return {"error": "UserID not found"}, 404

    # Sauvegarder user_id dans la session
    session['user_id'] = user_id
    return {"message": "User found, proceed to verification"}, 200


def verify_logic(entered_code):
    correct_code = "123456"  # ⚠️ à remplacer par un générateur OTP réel
    user_id = session.get('user_id')

    if not user_id:
        return {"error": "Session expired, please login again"}, 401

    if entered_code == correct_code:
        account = AccountData.objects(userID=user_id).first()
        return {"message": "Login successful", "account": account.to_mongo().to_dict()}, 200
    else:
        return {"error": "Invalid code"}, 401



# Note: In a real application, use a secure OTP generation and validation mechanism.