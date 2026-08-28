import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Secret Key and Database Config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'jackiecutz-secret-golden-key-2026')
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', f'sqlite:///{os.path.join(basedir, "../instance/barbershop.db")}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        # Ensure database tables exist
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)