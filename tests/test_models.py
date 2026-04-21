import datetime
import pytest
from app import db
from app.models import User, Ingredient, Expense, ShoppingItem


# --- Helpers ---

def make_user(full_name="Test User", email="test@example.com") -> User:
    user = User(full_name=full_name, email=email, password_hash="hashed")
    db.session.add(user)
    db.session.commit()
    return user


# --- User ---

def test_user_created(app):
    """User is saved with correct fields."""
    user = make_user()
    assert user.id is not None
    assert user.full_name == "Test User"
    assert user.email == "test@example.com"


def test_user_get_id_returns_string(app):
    """get_id() must return a string for Flask-Login."""
    user = make_user()
    assert isinstance(user.get_id(), str)


def test_user_delete_cascades(app):
    """Deleting a user removes all related ingredients."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id, name="Milk", quantity=1.0, unit="l", category="Dairy"
    )
    db.session.add(ingredient)
    db.session.commit()

    db.session.delete(user)
    db.session.commit()

    assert Ingredient.query.count() == 0


# --- Ingredient ---

def test_ingredient_created(app):
    """Ingredient is saved with correct fields."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id, name="Tomato", quantity=3.0, unit="pcs", category="Vegetables"
    )
    db.session.add(ingredient)
    db.session.commit()

    assert ingredient.id is not None
    assert ingredient.name == "Tomato"
    assert ingredient.is_low_stock is False


def test_expiry_status_fresh(app):
    """Ingredient expiring in more than 7 days returns 'fresh'."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id,
        name="Cheese",
        quantity=1.0,
        unit="kg",
        category="Dairy",
        expiry_date=datetime.date.today() + datetime.timedelta(days=8),
    )
    assert ingredient.expiry_status == "fresh"


def test_expiry_status_warning(app):
    """Ingredient expiring within 7 days returns 'warning'."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id,
        name="Yogurt",
        quantity=1.0,
        unit="pcs",
        category="Dairy",
        expiry_date=datetime.date.today() + datetime.timedelta(days=5),
    )
    assert ingredient.expiry_status == "warning"


def test_expiry_status_expired(app):
    """Ingredient past its expiry date returns 'expired'."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id,
        name="Old Milk",
        quantity=1.0,
        unit="l",
        category="Dairy",
        expiry_date=datetime.date.today() - datetime.timedelta(days=1),
    )
    assert ingredient.expiry_status == "expired"


def test_expiry_status_expires_today(app):
    """Ingredient expiring today returns 'expired'."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id,
        name="Milk",
        quantity=1.0,
        unit="l",
        category="Dairy",
        expiry_date=datetime.date.today(),
    )
    assert ingredient.expiry_status == "expired"


def test_expiry_status_no_date(app):
    """Ingredient with no expiry date returns 'fresh'."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id, name="Salt", quantity=500.0, unit="g", category="Spices"
    )
    assert ingredient.expiry_status == "fresh"


# --- Expense ---

def test_expense_created(app):
    """Expense is saved with correct week and year."""
    user = make_user()
    today = datetime.date.today()
    iso = today.isocalendar()

    expense = Expense(
        user_id=user.id,
        amount=12.50,
        description="Groceries",
        date=today,
        week_number=iso.week,
        year=iso.year,
    )
    db.session.add(expense)
    db.session.commit()

    assert expense.id is not None
    assert expense.amount == 12.50
    assert expense.week_number == iso.week


# --- ShoppingItem ---

def test_shopping_item_custom(app):
    """Custom shopping item has no linked ingredient."""
    user = make_user()
    item = ShoppingItem(user_id=user.id, name="Bread")
    db.session.add(item)
    db.session.commit()

    assert item.ingredient_id is None
    assert item.is_checked is False


def test_shopping_item_linked_to_ingredient(app):
    """Shopping item can be linked to a low-stock ingredient."""
    user = make_user()
    ingredient = Ingredient(
        user_id=user.id, name="Eggs", quantity=2.0, unit="pcs",
        category="Other", is_low_stock=True
    )
    db.session.add(ingredient)
    db.session.commit()

    item = ShoppingItem(user_id=user.id, name="Eggs", ingredient_id=ingredient.id)
    db.session.add(item)
    db.session.commit()

    assert item.ingredient_id == ingredient.id
    assert item.ingredient.name == "Eggs"