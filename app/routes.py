import re
import datetime
from flask import Blueprint, redirect, render_template, request, flash, url_for, abort
from flask_login import login_required, logout_user, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
from app.models import User, Ingredient, ShoppingItem, Expense

main = Blueprint("main", __name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

CATEGORIES = ["Vegetables", "Dairy", "Meat", "Condiments", "Drinks", "Other"]
UNITS = ["g", "kg", "ml", "l", "pcs"]


def get_dates() -> dict:
    today = datetime.date.today()
    max_date = today.replace(year=today.year + 10)
    return {"today": today.isoformat(), "max_date": max_date.isoformat()}


def get_total_spent() -> float:
    today = datetime.date.today()
    iso = today.isocalendar()
    total = db.session.query(db.func.sum(Expense.amount)).filter_by(
        user_id=current_user.id,
        week_number=iso.week,
        year=iso.year,
    ).scalar() or 0.0
    return total


@main.route("/")
@login_required
def index():
    filter_mode = request.args.get("filter", "")
    active_category = request.args.get("category", "all")
    base_query = Ingredient.query.filter_by(user_id=current_user.id)

    if filter_mode == "use-first":
        cutoff = datetime.date.today() + datetime.timedelta(days=7)
        ingredients = (
            base_query
            .filter(Ingredient.expiry_date.isnot(None), Ingredient.expiry_date <= cutoff)
            .order_by(Ingredient.expiry_date.asc())
            .all()
        )
    elif active_category != "all":
        ingredients = (
            base_query
            .filter_by(category=active_category)
            .order_by(Ingredient.id.desc())
            .all()
        )
    else:
        ingredients = base_query.order_by(Ingredient.id.desc()).all()

    return render_template(
        "ingredients/dashboard.html",
        ingredients=ingredients,
        categories=CATEGORIES,
        units=UNITS,
        active_category=active_category,
        filter_mode=filter_mode,
        **get_dates(),
    )


@main.route("/ingredient/add", methods=["GET", "POST"])
@login_required
def ingredient_add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        unit = request.form.get("unit", "").strip()
        category = request.form.get("category", "").strip()
        expiry_date_str = request.form.get("expiry_date", "").strip()

        if not name:
            flash("Name is required.", "error")
            return render_template("ingredients/ingredient_add.html",
                                   categories=CATEGORIES, units=UNITS, **get_dates())
        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Quantity must be a positive number.", "error")
            return render_template("ingredients/ingredient_add.html",
                                   categories=CATEGORIES, units=UNITS, **get_dates())

        if unit not in UNITS:
            flash("Please select a valid unit.", "error")
            return render_template("ingredients/ingredient_add.html",
                                   categories=CATEGORIES, units=UNITS, **get_dates())

        if category not in CATEGORIES:
            flash("Please select a valid category.", "error")
            return render_template("ingredients/ingredient_add.html",
                                   categories=CATEGORIES, units=UNITS, **get_dates())

        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.date.fromisoformat(expiry_date_str)
                if expiry_date < datetime.date.today():
                    flash("Expiry date must not be in the past.", "error")
                    return render_template("ingredients/ingredient_add.html",
                                           categories=CATEGORIES, units=UNITS, **get_dates())
            except ValueError:
                flash("Invalid expiry date.", "error")
                return render_template("ingredients/ingredient_add.html",
                                       categories=CATEGORIES, units=UNITS, **get_dates())

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
        return redirect(url_for("main.index"))

    return render_template("ingredients/ingredient_add.html",
                           categories=CATEGORIES, units=UNITS, **get_dates())


@main.route("/ingredient/<int:id>/edit", methods=["GET", "POST"])
@login_required
def ingredient_edit(id: int):
    ingredient = db.session.get(Ingredient, id)
    if ingredient is None:
        abort(404)
    if ingredient.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        quantity = request.form.get("quantity", "").strip()
        unit = request.form.get("unit", "").strip()
        category = request.form.get("category", "").strip()
        expiry_date_str = request.form.get("expiry_date", "").strip()

        if not name:
            flash("Name is required.", "error")
            return render_template("ingredients/ingredient_edit.html",
                                   ingredient=ingredient, categories=CATEGORIES,
                                   units=UNITS, **get_dates())
        try:
            quantity = float(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Quantity must be a positive number.", "error")
            return render_template("ingredients/ingredient_edit.html",
                                   ingredient=ingredient, categories=CATEGORIES,
                                   units=UNITS, **get_dates())

        if unit not in UNITS:
            flash("Please select a valid unit.", "error")
            return render_template("ingredients/ingredient_edit.html",
                                   ingredient=ingredient, categories=CATEGORIES,
                                   units=UNITS, **get_dates())

        if category not in CATEGORIES:
            flash("Please select a valid category.", "error")
            return render_template("ingredients/ingredient_edit.html",
                                   ingredient=ingredient, categories=CATEGORIES,
                                   units=UNITS, **get_dates())

        expiry_date = None
        if expiry_date_str:
            try:
                expiry_date = datetime.date.fromisoformat(expiry_date_str)
            except ValueError:
                flash("Invalid expiry date.", "error")
                return render_template("ingredients/ingredient_edit.html",
                                       ingredient=ingredient, categories=CATEGORIES,
                                       units=UNITS, **get_dates())

        ingredient.name = name
        ingredient.quantity = quantity
        ingredient.unit = unit
        ingredient.category = category
        ingredient.expiry_date = expiry_date
        ingredient.is_low_stock = request.form.get("is_low_stock") == "on"
        db.session.commit()

        flash(f'"{name}" has been updated.', "success")
        return redirect(url_for("main.index"))

    return render_template("ingredients/ingredient_edit.html",
                           ingredient=ingredient, categories=CATEGORIES,
                           units=UNITS, **get_dates())


@main.route('/ingredient/<int:id>/quantity', methods=['POST'])
@login_required
def ingredient_update_quantity(id: int):
    ingredient = db.session.get(Ingredient, id)
    if ingredient is None:
        abort(404)
    if ingredient.user_id != current_user.id:
        return {'error': 'Forbidden'}, 403

    action = request.json.get('action')
    step = request.json.get('step', 1)

    if action == 'increase':
        ingredient.quantity += step
    elif action == 'decrease':
        ingredient.quantity = max(0, ingredient.quantity - step)

    db.session.commit()
    return {'quantity': ingredient.quantity, 'is_low_stock': ingredient.is_low_stock}


@main.route('/ingredient/<int:id>/delete', methods=['POST'])
@login_required
def ingredient_delete(id: int):
    ingredient = db.session.get(Ingredient, id)
    if ingredient is None:
        abort(404)
    if ingredient.user_id != current_user.id:
        abort(403)

    db.session.delete(ingredient)
    db.session.commit()

    flash(f'"{ingredient.name}" has been removed.', 'success')
    return redirect(url_for('main.index'))


@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name:
            flash("Full name is required.", "error")
            return render_template("auth/register.html")
        if not EMAIL_REGEX.match(email):
            flash("Please enter a valid email address.", "error")
            return render_template("auth/register.html")
        if not password:
            flash("Password is required.", "error")
            return render_template("auth/register.html")
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return redirect(url_for("main.register"))

        user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("main.login", registered="1"))

    return render_template("auth/register.html")


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html")

        login_user(user)
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.index"))

    return render_template("auth/login.html")


@main.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


# ── Shopping List Routes (US11, US12, US14, US16) ──

@main.route("/shopping-list", methods=["GET", "POST"])
@login_required
def shopping_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        qty_amount = request.form.get("qty_amount", "").strip()
        qty_unit = request.form.get("qty_unit", "").strip()
        quantity = f"{qty_amount} {qty_unit}".strip() if qty_amount else None
        ingredient_id = request.form.get("ingredient_id", "").strip()

        if not name:
            flash("Item name is required.", "error")
            return redirect(url_for("main.shopping_list"))

        if ingredient_id:
            existing = ShoppingItem.query.filter_by(
                user_id=current_user.id,
                ingredient_id=int(ingredient_id),
            ).first()
            if existing:
                return redirect(url_for("main.shopping_list"))

        item = ShoppingItem(
            user_id=current_user.id,
            name=name,
            quantity=quantity if quantity else "1",
            ingredient_id=int(ingredient_id) if ingredient_id else None,
        )
        db.session.add(item)
        db.session.commit()
        return redirect(url_for("main.shopping_list"))

    # GET
    items = ShoppingItem.query.filter_by(user_id=current_user.id).order_by(ShoppingItem.id.asc()).all()

    on_list_ids = {item.ingredient_id for item in items if item.ingredient_id}
    suggestions_query = Ingredient.query.filter_by(user_id=current_user.id, is_low_stock=True)
    if on_list_ids:
        suggestions_query = suggestions_query.filter(~Ingredient.id.in_(on_list_ids))
    suggestions = suggestions_query.all()

    today = datetime.date.today()
    today_str = today.strftime("%A %-d %B").upper()

    return render_template(
        "shopping_list.html",
        items=items,
        suggestions=suggestions,
        today_str=today_str,
        today_date=today,
        budget=current_user.weekly_budget or 0.0,
        total_spent=get_total_spent(),
    )


@main.route("/shopping-list/toggle/<int:id>", methods=["POST"])
@login_required
def shopping_list_toggle(id: int):
    item = db.session.get(ShoppingItem, id)
    if item is None:
        abort(404)
    if item.user_id != current_user.id:
        abort(403)

    item.is_checked = not item.is_checked

    if item.is_checked:
        # Reset is_low_stock on linked ingredient
        if item.ingredient_id:
            ingredient = db.session.get(Ingredient, item.ingredient_id)
            if ingredient:
                ingredient.is_low_stock = False

        # Record expense if price provided
        data = request.get_json(silent=True) or {}
        price_str = str(data.get("price", "")).strip()
        if price_str:
            try:
                amount = float(price_str)
                if amount > 0:
                    item.price = amount
                    expense = Expense(
                        user_id=current_user.id,
                        amount=amount,
                        date=datetime.date.today(),
                        week_number=datetime.date.today().isocalendar().week,
                        year=datetime.date.today().isocalendar().year,
                    )
                    db.session.add(expense)
            except ValueError:
                pass
    else:
        item.price = None  # reset ตอน uncheck

    db.session.commit()
    return {"is_checked": item.is_checked, "total_spent": get_total_spent()}, 200


@main.route("/shopping-list/delete/<int:id>", methods=["POST"])
@login_required
def shopping_list_delete(id: int):
    item = db.session.get(ShoppingItem, id)
    if item is None:
        abort(404)
    if item.user_id != current_user.id:
        abort(403)

    if item.price:
        today = datetime.date.today()
        iso = today.isocalendar()
        expense = Expense.query.filter_by(
            user_id=current_user.id,
            amount=item.price,
            week_number=iso.week,
            year=iso.year,
        ).first()
        if expense:
            db.session.delete(expense)

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("main.shopping_list"))
    item = db.session.get(ShoppingItem, id)
    if item is None:
        abort(404)

    if item.user_id != current_user.id:
        abort(403)

    if item.ingredient_id:
        ingredient = db.session.get(Ingredient, item.ingredient_id)
        if ingredient:
            ingredient.is_low_stock = False

    if item.price:
        today = datetime.date.today()
        iso = today.isocalendar()
        expense = Expense.query.filter_by(
            user_id=current_user.id,
            amount=item.price,
            week_number=iso.week,
            year=iso.year,
        ).first()
        if expense:
            db.session.delete(expense)

    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("main.shopping_list"))


@main.route("/shopping-list/quantity/<int:id>", methods=["POST"])
@login_required
def shopping_list_update_quantity(id: int):
    item = db.session.get(ShoppingItem, id)
    if item is None:
        abort(404)
    if item.user_id != current_user.id:
        abort(403)

    action = request.json.get("action")
    if item.quantity:
        parts = item.quantity.split(" ", 1)
        try:
            num = float(parts[0])
            unit = parts[1] if len(parts) > 1 else ""
            if action == "increase":
                num += 1
            elif action == "decrease" and num > 1:
                num -= 1
            num_display = int(num) if num == int(num) else num
            item.quantity = f"{num_display} {unit}".strip()
        except ValueError:
            pass
    db.session.commit()
    return {"quantity": item.quantity}, 200


@main.route("/shopping-list/clear", methods=["POST"])
@login_required
def shopping_list_clear():
    checked_items = ShoppingItem.query.filter_by(
        user_id=current_user.id, is_checked=True
    ).all()

    for item in checked_items:
        if item.ingredient_id:
            ingredient = db.session.get(Ingredient, item.ingredient_id)
            if ingredient:
                ingredient.is_low_stock = False
        db.session.delete(item)

    db.session.commit()
    flash("Completed items cleared.", "success")
    return redirect(url_for("main.shopping_list"))


@main.route("/shopping-list/set-budget", methods=["POST"])
@login_required
def set_budget():
    amount_str = request.form.get("budget", "").strip()
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        flash("Budget must be a positive number.", "error")
        return redirect(url_for("main.shopping_list"))

    current_user.weekly_budget = amount
    db.session.commit()
    flash("Weekly budget updated.", "success")
    return redirect(url_for("main.shopping_list"))


@main.route("/shopping-list/clear-budget", methods=["POST"])
@login_required
def clear_budget():
    current_user.weekly_budget = 0.0

    today = datetime.date.today()
    iso = today.isocalendar()
    Expense.query.filter_by(
        user_id=current_user.id,
        week_number=iso.week,
        year=iso.year,
    ).delete()

    db.session.commit()
    return redirect(url_for("main.shopping_list"))