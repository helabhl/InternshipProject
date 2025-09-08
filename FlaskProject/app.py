from flask import Flask, render_template
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, timezone

# --- Load environment variables ---
load_dotenv()

# --- Flask app setup ---
app = Flask(__name__)
CORS(app)  # Allow all origins
app.secret_key = os.getenv("SECRET_KEY")

# --- MongoDB connection ---
MONGO_URI = os.getenv("MONGO_URI") 
DB_NAME = os.getenv("DB_NAME") or "db"

client = MongoClient(MONGO_URI)
app.db = client[DB_NAME]

# --- Blueprints ---
from routes.accountRoute import accounts_bp
from routes.quizRoute import quiz_bp
from routes.authRoute import auth_bp
from routes.adminRoute import admin_bp
from routes.attemptRoute import attempts_bp
from routes.performanceRoute import performance_bp

app.register_blueprint(accounts_bp)
app.register_blueprint(quiz_bp)
app.register_blueprint(attempts_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(performance_bp)

# --- Scheduler function ---
def mark_timeout_attempts():
    """
    Mark all attempts as timed out if they started more than 1 hour ago
    and are not completed, failed, aborted, or timed out yet.
    """
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    attempts = app.db.attempts.find({
        "completed": 0,
        "failed": 0,
        "aborted": 0,
        "timeout": 0,
        "start_time": {"$lt": one_hour_ago}
    })

    for attempt in attempts:
        app.db.attempts.update_one(
            {"_id": attempt["_id"]},
            {"$set": {
                "timeout": 1,
                "end_time": attempt["start_time"] + timedelta(hours=1),
                "time_spent": 3600
            }}
        )

# --- Start scheduler ---
scheduler = BackgroundScheduler()
scheduler.add_job(func=mark_timeout_attempts, trigger="interval", minutes=5)
scheduler.start()

# --- Flask CLI command to create admin ---
@app.cli.command("create-admin")
def create_admin():
    from werkzeug.security import generate_password_hash

    email = input("Email admin: ")
    password = input("Mot de passe: ")

    admin_doc = {
        "email": email,
        "password_hash": generate_password_hash(password)
    }

    app.db.admins.insert_one(admin_doc)
    print("✅ Admin créé avec succès")

# --- Routes ---
@app.route("/home")
def home():
    return render_template("users/home.html")

@app.route("/dashboard")
def dashboard():
    return render_template("admin/dashboard.html")

@app.route("/quizzes")
def quizzes():
    return render_template("users/quiz.html")

@app.route("/quiz")
def quiz():
    return render_template("quiz.html")

@app.route("/subject")
def subject():
    return render_template("users/subjects.html")

# --- Run the app ---
if __name__ == "__main__":
    app.run(debug=True)
