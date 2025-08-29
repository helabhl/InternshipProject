from flask import Flask, render_template
from pymongo import MongoClient
import config
from models.attempt import AttemptData
from routes.accounts import accounts_bp
from routes.quizzes import quiz_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.attempts import attempts_bp
from routes.performances import performance_bp
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Autorise toutes les origines

# ou bien restrictif :
# CORS(app, origins=["http://127.0.0.1:5000"])


load_dotenv()  # Charge les variables d’environnement dans os.environ

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
# Connect to MongoDB
client = MongoClient(config.MONGO_URI)
app.db = client[config.DB_NAME]



def mark_abandoned_attempts():
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    attempts = AttemptData.objects(
        completed=0,
        failed=0,
        abandoned=0,
        start_time__lt=one_hour_ago
    )
    for attempt in attempts:
        attempt.abandoned = 1
        attempt.end_time = attempt.start_time + timedelta(hours=1)
        attempt.time_spent = 3600
        attempt.save()

# 🔹 Scheduler qui vérifie toutes les 5 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=mark_abandoned_attempts, trigger="interval", minutes=5)
scheduler.start()


# Register blueprints
app.register_blueprint(accounts_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(attempts_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(performance_bp)



# Commande Flask CLI
@app.cli.command("create-admin")
def create_admin():
    from werkzeug.security import generate_password_hash
    from models.admin import Admin

    email = input("Email admin: ")
    password = input("Mot de passe: ")
    admin = Admin(email=email, password_hash=generate_password_hash(password))
    admin.save()
    print("✅ Admin créé avec succès")


@app.route("/home")
def home():
    return render_template("users/home.html")


@app.route("/dashboard")
def dd():
    return render_template("users/base.html")


@app.route("/")
def d():
    return render_template("users/dash.html")

@app.route("/api-test")
def api_test():
    return render_template("api_test.html")


if __name__ == "__main__":
    app.run(debug=True)
