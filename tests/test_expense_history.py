import datetime
import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Expense


# --- Helpers ---

def make_user(full_name="Test User", email="test@example.com", password="password123") -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email="test@example.com", password="password123"):
    client.post("/login", data={"email": email, "password": password})


def make_expense(user_id: int, amount: float, description: str = None,
                 week_number: int = 20, year: int = 2026,
                 date: datetime.date = None) -> Expense:
    expense = Expense(
        user_id=user_id,
        amount=amount,
        description=description,
        date=date or datetime.date(2026, 5, 16),
        week_number=week_number,
        year=year,
    )
    db.session.add(expense)
    db.session.commit()
    return expense


# --- Access control ---

def test_expense_history_requires_login(client):
    """/expense-history redirects to login if not authenticated."""
    response = client.get("/expense-history", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_expense_history_loads_for_authenticated_user(client, app):
    """/expense-history returns 200 for a logged-in user."""
    with app.app_context():
        make_user()

    login(client)
    response = client.get("/expense-history")
    assert response.status_code == 200


# --- Display ---

def test_expense_history_shows_week_number(client, app):
    """Week number is visible on the page."""
    with app.app_context():
        user = make_user()
        make_expense(user.id, amount=5.00, week_number=20, year=2026)

    login(client)
    response = client.get("/expense-history")
    assert b"Week 20" in response.data


def test_expense_history_shows_total(client, app):
    """Total per week is correctly summed and displayed."""
    with app.app_context():
        user = make_user()
        make_expense(user.id, amount=10.00, week_number=20, year=2026)
        make_expense(user.id, amount=5.50, week_number=20, year=2026)

    login(client)
    response = client.get("/expense-history")
    assert b"15.50" in response.data


def test_expense_history_shows_description(client, app):
    """Item name is shown as expense description."""
    with app.app_context():
        user = make_user()
        make_expense(user.id, amount=3.99, description="Apples", week_number=20, year=2026)

    login(client)
    response = client.get("/expense-history")
    assert b"Apples" in response.data


def test_expense_history_empty_state(client, app):
    """Empty state message shown when user has no expenses."""
    with app.app_context():
        make_user()

    login(client)
    response = client.get("/expense-history")
    assert b"No expenses recorded yet" in response.data


# --- Grouping & sorting ---

def test_expense_history_groups_by_week(client, app):
    """Expenses from different weeks appear as separate groups."""
    with app.app_context():
        user = make_user()
        make_expense(user.id, amount=4.00, week_number=19, year=2026,
                     date=datetime.date(2026, 5, 9))
        make_expense(user.id, amount=6.00, week_number=20, year=2026,
                     date=datetime.date(2026, 5, 16))

    login(client)
    response = client.get("/expense-history")
    assert b"Week 19" in response.data
    assert b"Week 20" in response.data


def test_expense_history_sorted_newest_first(client, app):
    """Most recent week appears before older weeks."""
    with app.app_context():
        user = make_user()
        make_expense(user.id, amount=4.00, week_number=19, year=2026)
        make_expense(user.id, amount=6.00, week_number=20, year=2026)

    login(client)
    response = client.get("/expense-history")
    html = response.data.decode()
    assert html.index("Week 20") < html.index("Week 19")


# --- Data isolation ---

def test_expense_history_only_shows_own_expenses(client, app):
    """User A cannot see User B's expenses."""
    with app.app_context():
        user_a = make_user(email="a@example.com")
        user_b = make_user(email="b@example.com", full_name="User B")
        make_expense(user_a.id, amount=9.99, description="User A item")
        make_expense(user_b.id, amount=1.23, description="User B secret")

    login(client, email="a@example.com")
    response = client.get("/expense-history")
    assert b"User A item" in response.data
    assert b"User B secret" not in response.data