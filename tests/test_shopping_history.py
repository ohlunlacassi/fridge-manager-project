import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, ShoppingItem, ShoppingHistory


# ── Helpers ──

def make_user(full_name="Test User", email="test@example.com",
              password="password123") -> User:
    user = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
        weekly_budget=0.0,
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email="test@example.com", password="password123"):
    return client.post("/login", data={"email": email, "password": password})


def make_history(user_id: int, name: str) -> ShoppingHistory:
    entry = ShoppingHistory(user_id=user_id, name=name)
    db.session.add(entry)
    db.session.commit()
    return entry


# ── Adding items saves to history ──

def test_adding_item_saves_to_history(client, app):
    """Adding a shopping item saves its name to ShoppingHistory."""
    with app.app_context():
        make_user()

    login(client)
    client.post("/shopping-list", data={
        "name": "Milk",
        "qty_amount": "1",
        "qty_unit": "l",
    })

    with app.app_context():
        entry = ShoppingHistory.query.filter_by(name="Milk").first()
        assert entry is not None


def test_adding_same_name_twice_saves_only_once(client, app):
    """Adding the same item name twice does not create duplicate history entries."""
    with app.app_context():
        make_user()

    login(client)
    client.post("/shopping-list",
                data={"name": "Eggs", "qty_amount": "", "qty_unit": ""})
    client.post("/shopping-list",
                data={"name": "Eggs", "qty_amount": "", "qty_unit": ""})

    with app.app_context():
        count = ShoppingHistory.query.filter_by(name="Eggs").count()
        assert count == 1


def test_adding_same_name_case_insensitive_saves_only_once(client, app):
    """History deduplication is case-insensitive."""
    with app.app_context():
        make_user()

    login(client)
    client.post("/shopping-list",
                data={"name": "Milk", "qty_amount": "", "qty_unit": ""})
    client.post("/shopping-list",
                data={"name": "milk", "qty_amount": "", "qty_unit": ""})

    with app.app_context():
        count = ShoppingHistory.query.count()
        assert count == 1


def test_history_is_user_isolated(client, app):
    with app.app_context():
        user_a = make_user(email="a@example.com")
        user_b = make_user(full_name="User B", email="b@example.com")
        make_history(user_a.id, "Tea")
        user_b_id = user_b.id  # ← เก็บ id ไว้ก่อน

    login(client, email="b@example.com")
    client.get("/shopping-list")

    with app.app_context():
        b_history = ShoppingHistory.query.filter_by(user_id=user_b_id).all()
        assert len(b_history) == 0


# ── Suggestions persist after item deleted ──

def test_suggestions_persist_after_item_deleted(client, app):
    """Autocomplete suggestions remain after the shopping item is deleted."""
    with app.app_context():
        make_user()

    login(client)
    client.post("/shopping-list",
                data={"name": "Mango", "qty_amount": "", "qty_unit": ""})

    with app.app_context():
        item = ShoppingItem.query.filter_by(name="Mango").first()
        item_id = item.id

    client.post(f"/shopping-list/delete/{item_id}", follow_redirects=False)

    with app.app_context():
        entry = ShoppingHistory.query.filter_by(name="Mango").first()
        assert entry is not None


def test_suggestion_names_shown_on_shopping_list_page(client, app):
    """Suggestion names from history are passed to the shopping list template."""
    with app.app_context():
        user = make_user()
        make_history(user.id, "Müsli")
        make_history(user.id, "Mango")

    login(client)
    response = client.get("/shopping-list")

    assert "Müsli".encode() in response.data
    assert b"Mango" in response.data

# ── Delete suggestion ──


def test_delete_suggestion_removes_from_history(client, app):
    """Deleting a suggestion removes it from ShoppingHistory."""
    with app.app_context():
        user = make_user()
        make_history(user.id, "Butter")

    login(client)
    response = client.post(
        "/shopping-list/suggestion/delete",
        json={"name": "Butter"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "deleted"

    with app.app_context():
        entry = ShoppingHistory.query.filter_by(name="Butter").first()
        assert entry is None


def test_delete_suggestion_only_affects_own_history(client, app):
    with app.app_context():
        user_a = make_user(email="a@example.com")
        user_b = make_user(full_name="User B", email="b@example.com")
        make_history(user_a.id, "Butter")
        make_history(user_b.id, "Butter")
        user_b_id = user_b.id  # ← เก็บ id ไว้ก่อน

    login(client, email="a@example.com")
    client.post(
        "/shopping-list/suggestion/delete",
        json={"name": "Butter"},
        content_type="application/json",
    )

    with app.app_context():
        b_entry = ShoppingHistory.query.filter_by(
            user_id=user_b_id, name="Butter").first()
        assert b_entry is not None


def test_delete_suggestion_requires_login(client):
    """Unauthenticated delete suggestion redirects to login."""
    response = client.post(
        "/shopping-list/suggestion/delete",
        json={"name": "Milk"},
        content_type="application/json",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
