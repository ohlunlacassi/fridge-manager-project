import datetime
import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Ingredient


# --- Helpers ---

def make_user(full_name="Test User", email="test@example.com", password="password123") -> User:
    """Create and persist a user with a properly hashed password."""
    user = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email="test@example.com", password="password123"):
    """Log in a user via the test client."""
    return client.post("/login", data={"email": email, "password": password})


# --- Dashboard ---

def test_dashboard_requires_login(client):
    """Unauthenticated access to / redirects to login."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_loads_after_login(client, app):
    """Dashboard returns 200 after login."""
    with app.app_context():
        make_user()
    login(client)
    response = client.get("/")
    assert response.status_code == 200


def test_dashboard_shows_only_own_ingredients(client, app):
    """User only sees their own ingredients — not another user's."""
    with app.app_context():
        user_a = make_user(email="a@example.com")
        user_b = make_user(full_name="User B", email="b@example.com")

        # Add ingredient for user A.
        ing_a = Ingredient(user_id=user_a.id, name="Apple", quantity=1.0, unit="pcs", category="Vegetables")
        # Add ingredient for user B.
        ing_b = Ingredient(user_id=user_b.id, name="Secret Stash", quantity=1.0, unit="pcs", category="Other")
        db.session.add_all([ing_a, ing_b])
        db.session.commit()

    # Log in as user A.
    login(client, email="a@example.com")
    response = client.get("/")

    assert b"Apple" in response.data
    assert b"Secret Stash" not in response.data


# --- Add Ingredient ---

def test_add_ingredient_page_loads(client, app):
    """Add ingredient page returns 200 when logged in."""
    with app.app_context():
        make_user()
    login(client)
    response = client.get("/ingredient/add")
    assert response.status_code == 200


def test_add_ingredient_success(client, app):
    """Valid ingredient is saved and redirects to dashboard."""
    with app.app_context():
        make_user()
    login(client)

    response = client.post("/ingredient/add", data={
        "name": "Milk",
        "quantity": "1",
        "unit": "l",
        "category": "Dairy",
        "expiry_date": (datetime.date.today() + datetime.timedelta(days=10)).isoformat(),
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/" in response.headers["Location"]

    with app.app_context():
        assert Ingredient.query.filter_by(name="Milk").first() is not None


def test_add_ingredient_missing_name(client, app):
    """Ingredient without a name shows an error."""
    with app.app_context():
        make_user()
    login(client)

    response = client.post("/ingredient/add", data={
        "name": "",
        "quantity": "1",
        "unit": "l",
        "category": "Dairy",
    }, follow_redirects=True)

    assert b"required" in response.data


def test_add_ingredient_invalid_quantity(client, app):
    """Ingredient with invalid quantity shows an error."""
    with app.app_context():
        make_user()
    login(client)

    response = client.post("/ingredient/add", data={
        "name": "Milk",
        "quantity": "-1",
        "unit": "l",
        "category": "Dairy",
    }, follow_redirects=True)

    assert b"positive" in response.data


def test_add_ingredient_past_expiry(client, app):
    """Ingredient with past expiry date shows an error."""
    with app.app_context():
        make_user()
    login(client)

    response = client.post("/ingredient/add", data={
        "name": "Old Milk",
        "quantity": "1",
        "unit": "l",
        "category": "Dairy",
        "expiry_date": (datetime.date.today() - datetime.timedelta(days=1)).isoformat(),
    }, follow_redirects=True)

    assert b"past" in response.data


def test_add_ingredient_requires_login(client):
    """Unauthenticated access to add ingredient redirects to login."""
    response = client.get("/ingredient/add", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    # --- Edit Ingredient ---

def make_ingredient(user_id: int, name: str = "Milk", quantity: float = 1.0,
                    unit: str = "l", category: str = "Dairy") -> Ingredient:
    """Create and persist an ingredient for a given user."""
    ing = Ingredient(user_id=user_id, name=name, quantity=quantity,
                     unit=unit, category=category)
    db.session.add(ing)
    db.session.commit()
    return ing


def test_edit_ingredient_success(client, app):
    """Valid edit saves changes and redirects to dashboard."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id)
        ing_id = ing.id

    login(client)
    response = client.post(f"/ingredient/{ing_id}/edit", data={
        "name": "Oat Milk",
        "quantity": "2",
        "unit": "l",
        "category": "Dairy",
        "expiry_date": "",
    }, follow_redirects=False)

    assert response.status_code == 302

    with app.app_context():
        updated = db.session.get(Ingredient, ing_id)
        assert updated.name == "Oat Milk"
        assert updated.quantity == 2.0


def test_edit_ingredient_missing_name(client, app):
    """Edit with empty name shows error."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id)
        ing_id = ing.id

    login(client)
    response = client.post(f"/ingredient/{ing_id}/edit", data={
        "name": "",
        "quantity": "1",
        "unit": "l",
        "category": "Dairy",
    }, follow_redirects=True)

    assert b"required" in response.data


def test_edit_ingredient_invalid_quantity(client, app):
    """Edit with negative quantity shows error."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id)
        ing_id = ing.id

    login(client)
    response = client.post(f"/ingredient/{ing_id}/edit", data={
        "name": "Milk",
        "quantity": "-5",
        "unit": "l",
        "category": "Dairy",
    }, follow_redirects=True)

    assert b"positive" in response.data


def test_edit_ingredient_forbidden(client, app):
    """User cannot edit another user's ingredient — returns 403."""
    with app.app_context():
        owner = make_user(email="owner@example.com")
        attacker = make_user(full_name="Attacker", email="attacker@example.com")
        ing = make_ingredient(owner.id)
        ing_id = ing.id

    login(client, email="attacker@example.com")
    response = client.post(f"/ingredient/{ing_id}/edit", data={
        "name": "Hacked",
        "quantity": "1",
        "unit": "l",
        "category": "Dairy",
    })

    assert response.status_code == 403


def test_edit_ingredient_requires_login(client, app):
    """Unauthenticated edit redirects to login."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id)
        ing_id = ing.id

    response = client.post(f"/ingredient/{ing_id}/edit", data={
        "name": "Milk",
        "quantity": "1",
        "unit": "l",
        "category": "Dairy",
    }, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# --- Update Quantity (fetch endpoint) ---

def test_update_quantity_increase(client, app):
    """Increase quantity via fetch endpoint."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, quantity=5.0)
        ing_id = ing.id

    login(client)
    response = client.post(f"/ingredient/{ing_id}/quantity",
                           json={"action": "increase", "step": 1})

    assert response.status_code == 200
    assert response.get_json()["quantity"] == 6.0


def test_update_quantity_decrease(client, app):
    """Decrease quantity via fetch endpoint."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, quantity=10.0)
        ing_id = ing.id

    login(client)
    response = client.post(f"/ingredient/{ing_id}/quantity",
                           json={"action": "decrease", "step": 5})

    assert response.status_code == 200
    assert response.get_json()["quantity"] == 5.0


def test_update_quantity_forbidden(client, app):
    """Cannot update another user's ingredient quantity."""
    with app.app_context():
        owner = make_user(email="owner@example.com")
        attacker = make_user(full_name="Attacker", email="attacker@example.com")
        ing = make_ingredient(owner.id)
        ing_id = ing.id

    login(client, email="attacker@example.com")
    response = client.post(f"/ingredient/{ing_id}/quantity",
                           json={"action": "increase", "step": 1})

    assert response.status_code == 403

# --- Delete Ingredient ---

def test_delete_ingredient_success(client, app):
    """Delete removes ingredient from database and redirects."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id)
        ing_id = ing.id

    login(client)
    response = client.post(f'/ingredient/{ing_id}/delete', follow_redirects=False)

    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(Ingredient, ing_id) is None


def test_delete_ingredient_forbidden(client, app):
    """User cannot delete another user's ingredient — returns 403."""
    with app.app_context():
        owner = make_user(email='owner@example.com')
        attacker = make_user(full_name='Attacker', email='attacker@example.com')
        ing = make_ingredient(owner.id)
        ing_id = ing.id

    login(client, email='attacker@example.com')
    response = client.post(f'/ingredient/{ing_id}/delete')

    assert response.status_code == 403

    with app.app_context():
        assert db.session.get(Ingredient, ing_id) is not None


def test_delete_ingredient_requires_login(client, app):
    """Unauthenticated delete redirects to login."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id)
        ing_id = ing.id

    response = client.post(f'/ingredient/{ing_id}/delete', follow_redirects=False)

    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_delete_ingredient_not_found(client, app):
    """Delete on non-existent ingredient returns 404."""
    with app.app_context():
        make_user()

    login(client)
    response = client.post('/ingredient/99999/delete')

    assert response.status_code == 404