from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    """User account — stores credentials and links to all user-owned data."""

    __tablename__ = "users"

    id: int = db.Column(db.Integer, primary_key=True)
    full_name: str = db.Column(db.String(100), nullable=False)
    email: str = db.Column(db.String(254), unique=True, nullable=False)
    password_hash: str = db.Column(db.String(256), nullable=False)
    weekly_budget: float = db.Column(db.Float, nullable=True, default=0.0)

    # Cascade delete removes related rows automatically when a user is deleted.
    ingredients = db.relationship(
        "Ingredient", back_populates="user", cascade="all, delete-orphan"
    )
    expenses = db.relationship(
        "Expense", back_populates="user", cascade="all, delete-orphan"
    )
    shopping_items = db.relationship(
        "ShoppingItem", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.full_name!r}>"