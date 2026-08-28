import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        import app.models  # Load models
        db.create_all()    # Initialize SQLite tables safely

    return app