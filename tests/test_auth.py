import pytest
from werkzeug.security import generate_password_hash
from app import db
from app.models import User


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


# --- Register ---

def test_register_page_loads(client):
    """Registration page returns 200."""
    response = client.get("/register")
    assert response.status_code == 200


def test_register_success(client, app):
    """Valid registration saves the user and redirects to login."""
    response = client.post("/register", data={
        "full_name": "New User",
        "email": "new@example.com",
        "password": "secret123",
        "confirm_password": "secret123",
    }, follow_redirects=False)

    # Should redirect to /login after successful registration.
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    with app.app_context():
        assert User.query.filter_by(email="new@example.com").first() is not None


def test_register_duplicate_email(client, app):
    """Registration with an existing email shows an error."""
    with app.app_context():
        make_user(email="taken@example.com")

    response = client.post("/register", data={
        "full_name": "Another User",
        "email": "taken@example.com",
        "password": "secret123",
        "confirm_password": "secret123",
    }, follow_redirects=True)

    assert b"already exists" in response.data


def test_register_password_mismatch(client):
    """Registration with mismatched passwords shows an error."""
    response = client.post("/register", data={
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "secret123",
        "confirm_password": "different",
    }, follow_redirects=True)

    assert b"do not match" in response.data


# --- Login ---

def test_login_page_loads(client):
    """Login page returns 200."""
    response = client.get("/login")
    assert response.status_code == 200


def test_login_success(client, app):
    """Valid credentials log the user in and redirect to index."""
    with app.app_context():
        make_user(email="user@example.com", password="password123")

    response = client.post("/login", data={
        "email": "user@example.com",
        "password": "password123",
    }, follow_redirects=False)

    # Should redirect to / after successful login.
    assert response.status_code == 302
    assert "/" in response.headers["Location"]


def test_login_wrong_password(client, app):
    """Wrong password shows an error message."""
    with app.app_context():
        make_user(email="user@example.com", password="correctpassword")

    response = client.post("/login", data={
        "email": "user@example.com",
        "password": "wrongpassword",
    }, follow_redirects=True)

    assert b"Invalid email or password" in response.data


def test_login_unknown_email(client):
    """Unknown email shows an error message."""
    response = client.post("/login", data={
        "email": "nobody@example.com",
        "password": "password123",
    }, follow_redirects=True)

    assert b"Invalid email or password" in response.data


# --- Logout ---

def test_logout_redirects_to_login(client, app):
    """Logging out redirects to the login page."""
    with app.app_context():
        make_user(email="user@example.com", password="password123")

    # Log in first.
    client.post("/login", data={
        "email": "user@example.com",
        "password": "password123",
    })

    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_logout_requires_login(client):
    """Unauthenticated access to /logout redirects to login."""
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]