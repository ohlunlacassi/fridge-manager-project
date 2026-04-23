import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

login_manager.login_view = "main.login"
login_manager.login_message = None


def create_app():
    app = Flask(__name__)

    # --- CONFIG ---
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SECRET_KEY"] = "dev"
    app.config["SQLALCHEMY_DATABASE_URI"] = \
        "sqlite:///" + os.path.join(basedir, "..", "instance", "fridge.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- INIT ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.models import User, Ingredient, Expense, ShoppingItem

    # --- REGISTER BLUEPRINT ---
    from .routes import main
    app.register_blueprint(main)

    return app


@login_manager.user_loader
def load_user(user_id: str):
    from app.models import User
    return User.query.get(int(user_id))