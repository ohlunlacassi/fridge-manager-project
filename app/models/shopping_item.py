from app import db

class ShoppingItem(db.Model):
    __tablename__ = "shopping_items"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name: str = db.Column(db.String(100), nullable=False)
    is_checked: bool = db.Column(db.Boolean, nullable=False, default=False)
    ingredient_id: int = db.Column(
        db.Integer, db.ForeignKey("ingredients.id"), nullable=True
    )
    quantity: str = db.Column(db.String(50), nullable=True)
    price: float = db.Column(db.Float, nullable=True)

    user = db.relationship("User", back_populates="shopping_items")
    ingredient = db.relationship("Ingredient", back_populates="shopping_items")

    def __repr__(self) -> str:
        return f"<ShoppingItem {self.name!r} checked={self.is_checked}>"