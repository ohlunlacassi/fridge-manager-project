import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Ingredient


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


def make_ingredient(user_id: int, name: str = "Milk",
                    quantity: float = 1.0, unit: str = "l") -> Ingredient:
    ing = Ingredient(
        user_id=user_id,
        name=name,
        quantity=quantity,
        unit=unit,
        category="Other",
    )
    db.session.add(ing)
    db.session.commit()
    return ing


# ── Restock by name (US22) ──

def test_restock_increases_existing_ingredient(client, app):
    """Restock increases quantity of matching ingredient."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, name="Milk", quantity=2.0)
        ing_id = ing.id

    login(client)
    response = client.post(
        "/ingredient/restock-by-name",
        json={"name": "Milk", "quantity": 3.0},
        content_type="application/json",
    )

    assert response.status_code == 200
    with app.app_context():
        updated = db.session.get(Ingredient, ing_id)
        assert updated.quantity == 5.0


def test_restock_case_insensitive_match(client, app):
    """Restock matches ingredient name case-insensitively."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, name="Brokkoli", quantity=1.0)
        ing_id = ing.id

    login(client)
    client.post(
        "/ingredient/restock-by-name",
        json={"name": "brokkoli", "quantity": 2.0},
        content_type="application/json",
    )

    with app.app_context():
        updated = db.session.get(Ingredient, ing_id)
        assert updated.quantity == 3.0


def test_restock_creates_new_ingredient_if_not_found(client, app):
    """Restock creates a new ingredient entry if name not found."""
    with app.app_context():
        make_user()

    login(client)
    response = client.post(
        "/ingredient/restock-by-name",
        json={"name": "Kiwi", "quantity": 5.0},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "created"

    with app.app_context():
        ing = Ingredient.query.filter_by(name="Kiwi").first()
        assert ing is not None
        assert ing.quantity == 5.0


def test_restock_invalid_quantity_returns_400(client, app):
    """Restock with invalid quantity returns 400."""
    with app.app_context():
        make_user()

    login(client)
    response = client.post(
        "/ingredient/restock-by-name",
        json={"name": "Milk", "quantity": -1.0},
        content_type="application/json",
    )

    assert response.status_code == 400


def test_restock_requires_login(client):
    """Unauthenticated restock redirects to login."""
    response = client.post(
        "/ingredient/restock-by-name",
        json={"name": "Milk", "quantity": 1.0},
        content_type="application/json",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_restock_only_affects_own_ingredients(client, app):
    """Restock only matches ingredients belonging to the logged-in user."""
    with app.app_context():
        user_a = make_user(email="a@example.com")
        user_b = make_user(full_name="User B", email="b@example.com")
        ing_b = make_ingredient(user_b.id, name="Milk", quantity=1.0)
        ing_b_id = ing_b.id

    login(client, email="a@example.com")
    client.post(
        "/ingredient/restock-by-name",
        json={"name": "Milk", "quantity": 5.0},
        content_type="application/json",
    )

    with app.app_context():
        # User B's ingredient should be unchanged
        ing_b = db.session.get(Ingredient, ing_b_id)
        assert ing_b.quantity == 1.0


# ── Reduce by name (delete checked item) ──

def test_reduce_decreases_ingredient_quantity(client, app):
    """Reduce subtracts quantity from matching ingredient."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, name="Reis", quantity=5.0)
        ing_id = ing.id

    login(client)
    client.post(
        "/ingredient/reduce-by-name",
        json={"name": "Reis", "quantity": 2.0},
        content_type="application/json",
    )

    with app.app_context():
        updated = db.session.get(Ingredient, ing_id)
        assert updated.quantity == 3.0


def test_reduce_does_not_go_below_zero(client, app):
    """Reduce clamps quantity to 0 if reduction exceeds current stock."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, name="Salz", quantity=1.0)
        ing_id = ing.id

    login(client)
    client.post(
        "/ingredient/reduce-by-name",
        json={"name": "Salz", "quantity": 10.0},
        content_type="application/json",
    )

    with app.app_context():
        updated = db.session.get(Ingredient, ing_id)
        assert updated.quantity == 0.0


def test_reduce_case_insensitive_match(client, app):
    """Reduce matches ingredient name case-insensitively."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, name="Möhren", quantity=3.0)
        ing_id = ing.id

    login(client)
    client.post(
        "/ingredient/reduce-by-name",
        json={"name": "möhren", "quantity": 1.0},
        content_type="application/json",
    )

    with app.app_context():
        updated = db.session.get(Ingredient, ing_id)
        assert updated.quantity == 2.0


def test_reduce_not_found_returns_200(client, app):
    """Reduce on non-existent ingredient returns 200 with not found status."""
    with app.app_context():
        make_user()

    login(client)
    response = client.post(
        "/ingredient/reduce-by-name",
        json={"name": "NonExistent", "quantity": 1.0},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.get_json()["status"] == "not found"


def test_reduce_invalid_quantity_returns_400(client, app):
    """Reduce with invalid quantity returns 400."""
    with app.app_context():
        make_user()

    login(client)
    response = client.post(
        "/ingredient/reduce-by-name",
        json={"name": "Milk", "quantity": 0},
        content_type="application/json",
    )

    assert response.status_code == 400


def test_reduce_requires_login(client):
    """Unauthenticated reduce redirects to login."""
    response = client.post(
        "/ingredient/reduce-by-name",
        json={"name": "Milk", "quantity": 1.0},
        content_type="application/json",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
