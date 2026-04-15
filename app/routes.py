import re
from flask import Blueprint, redirect, render_template, request, flash, url_for
from flask_login import login_required, logout_user, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User

main = Blueprint("main", __name__)

# Simple regex for email format validation.
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@main.route("/")
@login_required
def index():
    return "Fridge Manager is running!"


@main.route("/register", methods=["GET", "POST"])
def register():
    """Show the registration form (GET) and process it (POST)."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name:
            flash("Full name is required.", "error")
            return render_template("register.html")

        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.", "error")
            return render_template("register.html")

        if not password:
            flash("Password is required.", "error")
            return render_template("register.html")

        # Server-side password match check (JS handles the client-side version).
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return redirect(url_for("main.register"))

        # Hash the password before storing — never store plain text.
        user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    """Show the login form (GET) and process it (POST)."""
    # Redirect already-logged-in users away from the login page.
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # Use check_password_hash to verify against the stored hash.
        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        login_user(user)
        # Redirect to the page the user originally tried to access, or index.
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.index"))

    return render_template("login.html")


@main.route("/logout")
@login_required
def logout():
    """Log the current user out and redirect to login."""
    logout_user()
    return redirect(url_for("main.login"))