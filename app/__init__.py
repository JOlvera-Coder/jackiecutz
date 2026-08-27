import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Secret Key & DB Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'jackiecutz-secret-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///jackiecutz.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Register Blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        # 1. Create all missing tables safely first
        db.create_all()
        
        # 2. Seed initial data safely inside app context
        _seed_data()

    return app

def _seed_data():
    from app.models import User, BarberService, Product, ExpenseCategory, Customer
    from werkzeug.security import generate_password_hash

    try:
        # Seed Owner / Stylist Account (Ivonne)
        owner = User.query.filter_by(username="ivonne").first()
        if not owner:
            owner = User(
                username="ivonne",
                email="ivonne@jackiecutz.com",
                password_hash=generate_password_hash("jackie2026"),
                is_admin=True
            )
            db.session.add(owner)

        # Seed Default Services
        if BarberService.query.count() == 0:
            services = [
                BarberService(name="Signature Haircut", price=35.0, category="Haircut", duration_minutes=30),
                BarberService(name="Beard Trim & Shape", price=20.0, category="Beard", duration_minutes=20),
                BarberService(name="Haircut & Beard Combo", price=50.0, category="Combo", duration_minutes=45),
                BarberService(name="Hot Towel Shave", price=30.0, category="Shave", duration_minutes=30),
                BarberService(name="Kids Haircut", price=25.0, category="Haircut", duration_minutes=25)
            ]
            db.session.bulk_save_objects(services)

        # Seed Default Expense Categories
        if ExpenseCategory.query.count() == 0:
            cats = [
                ExpenseCategory(name="Supplies & Blades"),
                ExpenseCategory(name="Studio Rent & Utilities"),
                ExpenseCategory(name="Equipment Maintenance"),
                ExpenseCategory(name="Marketing & Signage")
            ]
            db.session.bulk_save_objects(cats)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Initial seeding skipped or already initialized:", e)

# Top-level instance for WSGI / CLI execution
app = create_app()