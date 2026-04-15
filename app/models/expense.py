import datetime
from app import db


class Expense(db.Model):
    """A single grocery purchase — used to track the user's weekly budget."""

    __tablename__ = "expenses"

    id: int = db.Column(db.Integer, primary_key=True)
    user_id: int = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount: float = db.Column(db.Float, nullable=False)
    description: str = db.Column(db.String(255), nullable=True)
    date: datetime.date = db.Column(db.Date, nullable=False, default=datetime.date.today)
    week_number: int = db.Column(db.Integer, nullable=False)
    year: int = db.Column(db.Integer, nullable=False)

    user = db.relationship("User", back_populates="expenses")

    def __repr__(self) -> str:
        return f"<Expense €{self.amount:.2f} week={self.week_number}/{self.year}>"