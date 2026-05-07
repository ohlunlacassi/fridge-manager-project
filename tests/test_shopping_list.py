import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Ingredient, ShoppingItem


# ── Helpers ──

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
    return client.post("/login", data={"email": email, "password": password})


def make_shopping_item(user_id: int, name: str = "Milk",
                       quantity: str = None, ingredient_id: int = None,
                       is_checked: bool = False) -> ShoppingItem:
    item = ShoppingItem(
        user_id=user_id,
        name=name,
        quantity=quantity,
        ingredient_id=ingredient_id,
        is_checked=is_checked,
    )
    db.session.add(item)
    db.session.commit()
    return item


def make_ingredient(user_id: int, name: str = "Milk",
                    is_low_stock: bool = False) -> Ingredient:
    ing = Ingredient(
        user_id=user_id,
        name=name,
        quantity=1.0,
        unit="l",
        category="Dairy",
        is_low_stock=is_low_stock,
    )
    db.session.add(ing)
    db.session.commit()
    return ing


# ── Shopping List Page (US11) ──

def test_shopping_list_requires_login(client):
    """Unauthenticated access redirects to login."""
    response = client.get("/shopping-list", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_shopping_list_loads(client, app):
    """Shopping list page returns 200 when logged in."""
    with app.app_context():
        make_user()
    login(client)
    response = client.get("/shopping-list")
    assert response.status_code == 200


def test_add_custom_item(client, app):
    """Custom item is saved to the shopping list."""
    with app.app_context():
        make_user()
    login(client)

    response = client.post("/shopping-list", data={
        "name": "Bread",
        "qty_amount": "",
        "qty_unit": "",
    }, follow_redirects=False)

    assert response.status_code == 302

    with app.app_context():
        item = ShoppingItem.query.filter_by(name="Bread").first()
        assert item is not None


def test_add_item_with_quantity(client, app):
    """Item with quantity is saved correctly."""
    with app.app_context():
        make_user()
    login(client)

    client.post("/shopping-list", data={
        "name": "Milk",
        "qty_amount": "2",
        "qty_unit": "l",
    })

    with app.app_context():
        item = ShoppingItem.query.filter_by(name="Milk").first()
        assert item is not None
        assert item.quantity == "2 l"


def test_add_item_missing_name(client, app):
    """Submitting without a name redirects back without saving."""
    with app.app_context():
        make_user()
    login(client)

    client.post("/shopping-list", data={"name": "", "qty_amount": "", "qty_unit": ""})

    with app.app_context():
        assert ShoppingItem.query.count() == 0


def test_shopping_list_shows_only_own_items(client, app):
    """User only sees their own shopping items."""
    with app.app_context():
        user_a = make_user(email="a@example.com")
        user_b = make_user(full_name="User B", email="b@example.com")
        make_shopping_item(user_a.id, name="My Tea")
        make_shopping_item(user_b.id, name="Their Coffee")

    login(client, email="a@example.com")
    response = client.get("/shopping-list")

    assert b"My Tea" in response.data
    assert b"Their Coffee" not in response.data


def test_suggestions_show_low_stock_ingredients(client, app):
    """Low stock ingredients appear in suggestions section."""
    with app.app_context():
        user = make_user()
        make_ingredient(user.id, name="Butter", is_low_stock=True)

    login(client)
    response = client.get("/shopping-list")
    assert b"Butter" in response.data


def test_suggestion_disappears_after_adding(client, app):
    """Once added to list, ingredient no longer appears in suggestions."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, name="Butter", is_low_stock=True)
        make_shopping_item(user.id, name="Butter", ingredient_id=ing.id)

    login(client)
    response = client.get("/shopping-list")

    # Butter appears in the list but not in suggestions twice
    assert response.data.count(b"Butter") == 1


# ── Toggle Check Off (US12) ──

def test_toggle_item_checks_it(client, app):
    """Toggling an unchecked item marks it as checked."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Eggs")
        item_id = item.id

    login(client)
    response = client.post(f"/shopping-list/toggle/{item_id}")

    assert response.status_code == 200
    assert response.get_json()["is_checked"] is True

    with app.app_context():
        updated = db.session.get(ShoppingItem, item_id)
        assert updated.is_checked is True


def test_toggle_item_unchecks_it(client, app):
    """Toggling a checked item marks it as unchecked."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Eggs", is_checked=True)
        item_id = item.id

    login(client)
    response = client.post(f"/shopping-list/toggle/{item_id}")

    assert response.get_json()["is_checked"] is False


def test_toggle_forbidden(client, app):
    """Cannot toggle another user's shopping item."""
    with app.app_context():
        owner = make_user(email="owner@example.com")
        attacker = make_user(full_name="Attacker", email="attacker@example.com")
        item = make_shopping_item(owner.id, name="Milk")
        item_id = item.id

    login(client, email="attacker@example.com")
    response = client.post(f"/shopping-list/toggle/{item_id}")
    assert response.status_code == 403


# ── Delete Item (US12) ──

def test_delete_item_removes_it(client, app):
    """Delete removes the item from the database."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Bread")
        item_id = item.id

    login(client)
    response = client.post(f"/shopping-list/delete/{item_id}",
                           follow_redirects=False)

    assert response.status_code == 302

    with app.app_context():
        assert db.session.get(ShoppingItem, item_id) is None


def test_delete_item_forbidden(client, app):
    """Cannot delete another user's shopping item."""
    with app.app_context():
        owner = make_user(email="owner@example.com")
        attacker = make_user(full_name="Attacker", email="attacker@example.com")
        item = make_shopping_item(owner.id, name="Milk")
        item_id = item.id

    login(client, email="attacker@example.com")
    response = client.post(f"/shopping-list/delete/{item_id}")

    assert response.status_code == 403

    with app.app_context():
        assert db.session.get(ShoppingItem, item_id) is not None


def test_delete_item_not_found(client, app):
    """Delete on non-existent item returns 404."""
    with app.app_context():
        make_user()
    login(client)
    response = client.post("/shopping-list/delete/99999")
    assert response.status_code == 404


# ── Clear Completed (US12) ──

def test_clear_removes_checked_items(client, app):
    """Clear completed removes all checked items."""
    with app.app_context():
        user = make_user()
        make_shopping_item(user.id, name="Eggs", is_checked=True)
        make_shopping_item(user.id, name="Milk", is_checked=True)
        make_shopping_item(user.id, name="Bread", is_checked=False)

    login(client)
    client.post("/shopping-list/clear")

    with app.app_context():
        remaining = ShoppingItem.query.filter_by(user_id=1).all()
        names = [i.name for i in remaining]
        assert "Eggs" not in names
        assert "Milk" not in names
        assert "Bread" in names


def test_clear_resets_low_stock_on_linked_ingredient(client, app):
    """Clearing a checked ingredient-linked item resets is_low_stock."""
    with app.app_context():
        user = make_user()
        ing = make_ingredient(user.id, name="Butter", is_low_stock=True)
        make_shopping_item(user.id, name="Butter",
                           ingredient_id=ing.id, is_checked=True)
        ing_id = ing.id

    login(client)
    client.post("/shopping-list/clear")

    with app.app_context():
        updated = db.session.get(Ingredient, ing_id)
        assert updated.is_low_stock is False


def test_clear_does_not_affect_unchecked_items(client, app):
    """Clear completed leaves unchecked items untouched."""
    with app.app_context():
        user = make_user()
        make_shopping_item(user.id, name="Apples", is_checked=False)

    login(client)
    client.post("/shopping-list/clear")

    with app.app_context():
        assert ShoppingItem.query.filter_by(name="Apples").first() is not None