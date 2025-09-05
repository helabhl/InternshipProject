from flask import Blueprint, request, session, flash, redirect, render_template, url_for
from werkzeug.security import check_password_hash
from models.admin import Admin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        admin = Admin.objects(email=email).first()
        if not admin or not check_password_hash(admin.password_hash, password):
            flash("Invalid email or password", "danger")
            return render_template("admin/login.html")

        session['admin_id'] = str(admin.id)
        flash("Welcome Admin!", "success")
        return render_template("admin/dashboard.html")

    return render_template("admin/login.html")
