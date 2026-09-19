import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()

def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    # Mail Configuration
    flask_app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    flask_app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    flask_app.config['MAIL_USE_TLS'] = True
    flask_app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    flask_app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    flask_app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

    db.init_app(flask_app)
    login_manager.init_app(flask_app)
    mail.init_app(flask_app)
    login_manager.login_view = 'main.login'

    # Register Flask-Login user_loader
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import main_bp
    flask_app.register_blueprint(main_bp)

    @flask_app.route('/.well-known/assetlinks.json')
    def asset_links():
        return send_from_directory(
            os.path.join(flask_app.root_path, 'static', '.well-known'),
            'assetlinks.json',
            mimetype='application/json'
        )

    with flask_app.app_context():
        db.create_all()

    return flask_app