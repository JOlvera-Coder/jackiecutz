import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    login_manager.login_view = 'main.login'

    from app.routes import main_bp
    flask_app.register_blueprint(main_bp)

    with flask_app.app_context():
        import app.models
        db.create_all()

    return flask_app