import datetime
from app import db


class Ingredient(db.Model):
    """A single item in the user's fridge or pantry."""

    __tablename__ = "ingredients"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name: str = db.Column(db.String(100), nullable=False)
    quantity: float = db.Column(db.Float, nullable=False, default=0.0)
    unit: str = db.Column(db.String(20), nullable=False, default="pcs")
    expiry_date: datetime.date = db.Column(db.Date, nullable=True)
    category: str = db.Column(db.String(50), nullable=False, default="Other")
    image_filename: str = db.Column(db.String(255), nullable=True)
    is_low_stock: bool = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="ingredients")
    shopping_items = db.relationship("ShoppingItem", back_populates="ingredient")

    @property
    def expiry_status(self) -> str:
        """Returns 'none' | 'fresh' | 'warning' | 'expired' for CSS class logic."""
        if self.expiry_date is None:
            return "fresh"
        
        delta = (self.expiry_date - datetime.date.today()).days
        if delta <= 0:
            return "expired"
        
        if delta <= 7:
            return "warning"
        return "fresh"

    def __repr__(self) -> str:
        return f"<Ingredient {self.name!r}>"