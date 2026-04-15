from app import db

class ShoppingItem(db.Model):
    """One entry on the shopping list.

    Can be auto-generated from a low-stock ingredient (ingredient_id set)
    or added manually by the user (ingredient_id is null).
    """

    __tablename__ = "shopping_items"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name: str = db.Column(db.String(100), nullable=False)
    is_checked: bool = db.Column(db.Boolean, nullable=False, default=False)
    ingredient_id: int = db.Column(
        db.Integer, db.ForeignKey("ingredients.id"), nullable=True
    )

    user = db.relationship("User", back_populates="shopping_items")
    ingredient = db.relationship("Ingredient", back_populates="shopping_items")

    def __repr__(self) -> str:
        return f"<ShoppingItem {self.name!r} checked={self.is_checked}>"