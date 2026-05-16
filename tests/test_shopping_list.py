import datetime
import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User, Ingredient, ShoppingItem, Expense
 
 
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
 
 
def make_expense(user_id: int, amount: float, weeks_ago: int = 0) -> Expense:
    """Create an expense for this week (or n weeks ago)."""
    today = datetime.date.today() - datetime.timedelta(weeks=weeks_ago)
    iso = today.isocalendar()
    expense = Expense(
        user_id=user_id,
        amount=amount,
        date=today,
        week_number=iso.week,
        year=iso.year,
    )
    db.session.add(expense)
    db.session.commit()
    return expense


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

# ── Set Budget (US14) ──
 
def test_set_budget_saves_to_user(client, app):
    """Setting budget updates user.weekly_budget."""
    with app.app_context():
        make_user()
    login(client)
    client.post("/shopping-list/set-budget", data={"budget": "50.00"})
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user.weekly_budget == 50.0
 
 
def test_set_budget_updates_existing_budget(client, app):
    """Setting a new budget overwrites the old one."""
    with app.app_context():
        user = make_user()
        user.weekly_budget = 100.0
        db.session.commit()
    login(client)
    client.post("/shopping-list/set-budget", data={"budget": "75.00"})
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user.weekly_budget == 75.0
 
 
def test_set_budget_invalid_negative(client, app):
    """Negative budget shows error and does not save."""
    with app.app_context():
        make_user()
    login(client)
    response = client.post("/shopping-list/set-budget",
                           data={"budget": "-10"},
                           follow_redirects=True)
    assert b"positive" in response.data
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user.weekly_budget == 0.0
 
 
def test_set_budget_invalid_zero(client, app):
    """Zero budget shows error and does not save."""
    with app.app_context():
        make_user()
    login(client)
    response = client.post("/shopping-list/set-budget",
                           data={"budget": "0"},
                           follow_redirects=True)
    assert b"positive" in response.data
 
 
def test_set_budget_requires_login(client):
    """Unauthenticated access redirects to login."""
    response = client.post("/shopping-list/set-budget",
                           data={"budget": "50"},
                           follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
 
 
# ── Clear Budget (US14) ──
 
def test_clear_budget_resets_to_zero(client, app):
    """Clear budget resets weekly_budget to 0.0."""
    with app.app_context():
        user = make_user()
        user.weekly_budget = 100.0
        db.session.commit()
    login(client)
    client.post("/shopping-list/clear-budget")
    with app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user.weekly_budget == 0.0
 
 
def test_clear_budget_requires_login(client):
    """Unauthenticated access redirects to login."""
    response = client.post("/shopping-list/clear-budget", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
 
 
# ── Budget Overview on Shopping List Page (US14) ──
 
def test_budget_displayed_on_shopping_list(client, app):
    """Budget amount is shown on shopping list page."""
    with app.app_context():
        user = make_user()
        user.weekly_budget = 80.0
        db.session.commit()
    login(client)
    response = client.get("/shopping-list")
    assert b"80.00" in response.data
 
 
def test_total_spent_shows_current_week_only(client, app):
    """Only expenses from the current ISO week are counted."""
    with app.app_context():
        user = make_user()
        make_expense(user.id, amount=30.0, weeks_ago=0)   # this week
        make_expense(user.id, amount=50.0, weeks_ago=1)   # last week
    login(client)
    response = client.get("/shopping-list")
    assert b"30.00" in response.data
    assert b"80.00" not in response.data
 
 
def test_over_budget_warning_shown(client, app):
    """Over-budget message is shown when expenses exceed budget."""
    with app.app_context():
        user = make_user()
        user.weekly_budget = 10.0
        db.session.commit()
        make_expense(user.id, amount=25.50)
    login(client)
    response = client.get("/shopping-list")
    assert b"Over budget" in response.data
    assert b"15.50" in response.data
 
 
def test_no_over_budget_when_under(client, app):
    """Over-budget message is not shown when under budget."""
    with app.app_context():
        user = make_user()
        user.weekly_budget = 100.0
        db.session.commit()
        make_expense(user.id, amount=25.0)
    login(client)
    response = client.get("/shopping-list")
    assert b"Over budget" not in response.data

    # ── US16: Record Purchase Expense ──
 
def test_toggle_with_price_creates_expense(client, app):
    """Checking off an item with a price creates an Expense record."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Milk")
        item_id = item.id
 
    login(client)
    client.post(
        f"/shopping-list/toggle/{item_id}",
        json={"price": "3.99"},
        content_type="application/json",
    )
 
    with app.app_context():
        expense = Expense.query.filter_by(user_id=1).first()
        assert expense is not None
        assert expense.amount == 3.99
 
 
def test_toggle_with_price_saves_to_item(client, app):
    """Checking off an item with a price saves price to ShoppingItem.price."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Bread")
        item_id = item.id
 
    login(client)
    client.post(
        f"/shopping-list/toggle/{item_id}",
        json={"price": "2.50"},
        content_type="application/json",
    )
 
    with app.app_context():
        updated = db.session.get(ShoppingItem, item_id)
        assert updated.price == 2.50
 
 
def test_toggle_without_price_creates_no_expense(client, app):
    """Checking off an item without price creates no Expense."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Salt")
        item_id = item.id
 
    login(client)
    client.post(
        f"/shopping-list/toggle/{item_id}",
        json={"price": ""},
        content_type="application/json",
    )
 
    with app.app_context():
        assert Expense.query.count() == 0
 
 
def test_toggle_with_zero_price_creates_no_expense(client, app):
    """Checking off with price 0 creates no Expense."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Salt")
        item_id = item.id
 
    login(client)
    client.post(
        f"/shopping-list/toggle/{item_id}",
        json={"price": "0"},
        content_type="application/json",
    )
 
    with app.app_context():
        assert Expense.query.count() == 0
 
 
def test_expense_linked_to_current_week(client, app):
    """Expense is recorded with correct ISO week and year."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Eggs")
        item_id = item.id
 
    login(client)
    client.post(
        f"/shopping-list/toggle/{item_id}",
        json={"price": "5.00"},
        content_type="application/json",
    )
 
    today = datetime.date.today()
    iso = today.isocalendar()
 
    with app.app_context():
        expense = Expense.query.filter_by(user_id=1).first()
        assert expense.week_number == iso.week
        assert expense.year == iso.year
        assert expense.date == today
 
 
def test_uncheck_resets_item_price(client, app):
    """Unchecking an item resets its price to None."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Butter", is_checked=True)
        item.price = 3.50
        db.session.commit()
        item_id = item.id
 
    login(client)
    client.post(
        f"/shopping-list/toggle/{item_id}",
        json={},
        content_type="application/json",
    )
 
    with app.app_context():
        updated = db.session.get(ShoppingItem, item_id)
        assert updated.price is None
 
 
def test_toggle_returns_total_spent(client, app):
    """Toggle response includes updated total_spent for current week."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Coffee")
        item_id = item.id
 
    login(client)
    response = client.post(
        f"/shopping-list/toggle/{item_id}",
        json={"price": "4.50"},
        content_type="application/json",
    )
 
    data = response.get_json()
    assert "total_spent" in data
    assert data["total_spent"] == 4.50
 
 
def test_multiple_expenses_sum_correctly(client, app):
    """Total spent sums all expenses for the current week."""
    with app.app_context():
        user = make_user()
        item1 = make_shopping_item(user.id, name="Milk")
        item2 = make_shopping_item(user.id, name="Bread")
        id1, id2 = item1.id, item2.id
 
    login(client)
    client.post(f"/shopping-list/toggle/{id1}", json={"price": "2.00"}, content_type="application/json")
    response = client.post(f"/shopping-list/toggle/{id2}", json={"price": "3.00"}, content_type="application/json")
 
    data = response.get_json()
    assert data["total_spent"] == 5.00
 
 
def test_expense_user_isolated(client, app):
    """Expenses are user-specific — other users' expenses not counted."""
    with app.app_context():
        user_a = make_user(email="a@example.com")
        user_b = make_user(full_name="User B", email="b@example.com")
 
        item_a = make_shopping_item(user_a.id, name="Tea")
        item_b = make_shopping_item(user_b.id, name="Coffee")
        id_a, id_b = item_a.id, item_b.id
 
    # User A buys tea for €5
    login(client, email="a@example.com")
    client.post(f"/shopping-list/toggle/{id_a}", json={"price": "5.00"}, content_type="application/json")
 
    # User B buys coffee for €3 — should not affect A's total
    client.post("/logout")
    login(client, email="b@example.com")
    client.post(f"/shopping-list/toggle/{id_b}", json={"price": "3.00"}, content_type="application/json")
 
    # Check user A's page shows only €5
    client.post("/logout")
    login(client, email="a@example.com")
    response = client.get("/shopping-list")
    assert b"5.00" in response.data
    assert b"8.00" not in response.data
 
def test_delete_item_removes_associated_expense(client, app):
    """Deleting a checked item with price removes its expense."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Milk", is_checked=True)
        item.price = 2.50
        db.session.commit()
        today = datetime.date.today()
        iso = today.isocalendar()
        expense = Expense(
            user_id=user.id,
            amount=2.50,
            date=today,
            week_number=iso.week,
            year=iso.year,
        )
        db.session.add(expense)
        db.session.commit()
        item_id = item.id

    login(client)
    client.post(f"/shopping-list/delete/{item_id}", follow_redirects=False)

    with app.app_context():
        assert Expense.query.count() == 0


def test_delete_item_without_price_leaves_expenses(client, app):
    """Deleting an item without price does not affect other expenses."""
    with app.app_context():
        user = make_user()
        item = make_shopping_item(user.id, name="Salt")
        db.session.commit()
        today = datetime.date.today()
        iso = today.isocalendar()
        expense = Expense(
            user_id=user.id,
            amount=5.00,
            date=today,
            week_number=iso.week,
            year=iso.year,
        )
        db.session.add(expense)
        db.session.commit()
        item_id = item.id

    login(client)
    client.post(f"/shopping-list/delete/{item_id}", follow_redirects=False)

    with app.app_context():
        assert Expense.query.count() == 1