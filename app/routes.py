import re
import datetime
from flask import Blueprint, redirect, render_template, request, flash, url_for, abort
from flask_login import login_required, logout_user, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User, Ingredient

main = Blueprint("main", __name__)

# Simple regex for email format validation.
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Predefined categories and units as specified in US5.
CATEGORIES = ["Gemüse", "Milchprodukte", "Fleisch", "Gewürze", "Getränke", "Sonstiges"]
UNITS = ["g", "kg", "ml", "l", "Stück"]


@main.route("/")
@login_required
def index():
    return redirect(url_for("main.ingredients"))


@main.route("/ingredients")
@login_required
def ingredients():
    """Show all ingredients belonging to the current user."""
    # Filter by user_id to ensure data isolation (US5).
    items = Ingredient.query.filter_by(user_id=current_user.id).all()
    return render_template("ingredients.html", ingredients=items)


@main.route("/ingredient/add", methods=["GET", "POST"])
@login_required
def ingredient_add():
    """Show the add ingredient form (GET) and process it (POST)."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        unit = request.form.get("unit", "").strip()
        category = request.form.get("category", "").strip()
        expiry_date_str = request.form.get("expiry_date", "").strip()

        # Validate required fields.
        if not name:
            flash("Name is required.", "error")
            return render_template("ingredient_add.html", categories=CATEGORIES, units=UNITS, today=datetime.date.today().isoformat())

        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Quantity must be a positive number.", "error")
            return render_template("ingredient_add.html", categories=CATEGORIES, units=UNITS, today=datetime.date.today().isoformat())

        if unit not in UNITS:
            flash("Please select a valid unit.", "error")
            return render_template("ingredient_add.html", categories=CATEGORIES, units=UNITS, today=datetime.date.today().isoformat())

        if category not in CATEGORIES:
            flash("Please select a valid category.", "error")
            return render_template("ingredient_add.html", categories=CATEGORIES, units=UNITS, today=datetime.date.today().isoformat())

        # Parse and validate expiry date — must not be in the past.
        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.date.fromisoformat(expiry_date_str)
                if expiry_date < datetime.date.today():
                    flash("Expiry date must not be in the past.", "error")
                    return render_template("ingredient_add.html", categories=CATEGORIES, units=UNITS, today=datetime.date.today().isoformat())
            except ValueError:
                flash("Invalid expiry date.", "error")
                return render_template("ingredient_add.html", categories=CATEGORIES, units=UNITS, today=datetime.date.today().isoformat())

        ingredient = Ingredient(
            user_id=current_user.id,
            name=name,
            quantity=quantity,
            unit=unit,
            category=category,
            expiry_date=expiry_date,
        )
        db.session.add(ingredient)
        db.session.commit()

        flash(f'"{name}" has been added to your inventory.', "success")
        return redirect(url_for("main.ingredients"))

    return render_template("ingredient_add.html", categories=CATEGORIES, units=UNITS, today=datetime.date.today().isoformat())


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