from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()
        _seed_data()

    return app

def _seed_data():
    from app.models import BarberService, User, Product, StudioExpense, ExpenseCategory
    
    # 1. Owner Setup
    owner = User.query.filter_by(username="ivonne").first()
    all_specs = ["Specialty Cut", "Haircut", "Hair Color", "Styling", "Beauty & Makeup", "Waxing", "Hair Treatment"]
    if owner is None:
        owner = User(
            username="ivonne",
            name="Ivonne Gonzalez",
            role="owner",
            is_active_stylist=True
        )
        owner.set_password("Jackiecutz2026!")
        owner.set_specialties(all_specs)
        db.session.add(owner)
    else:
        owner.set_specialties(all_specs)

    # 2. Services Seed
    if BarberService.query.count() == 0:
        default_services = [
            BarberService(name="Men & Boys Specialty Cut", category="Specialty Cut", price=25.00, duration_minutes=20),
            BarberService(name="Women & Girls Haircut", category="Haircut", price=30.00, duration_minutes=25),
            BarberService(name="Color & Highlights", category="Hair Color", price=85.00, duration_minutes=90),
            BarberService(name="Hairstyles / Updos", category="Styling", price=50.00, duration_minutes=90),
            BarberService(name="Professional Makeup", category="Beauty & Makeup", price=65.00, duration_minutes=45),
            BarberService(name="Waxing Services (Eyebrows/Lip)", category="Waxing", price=5.00, duration_minutes=15),
            BarberService(name="Intensive Deep Conditioning Treatment", category="Hair Treatment", price=10.00, duration_minutes=30)
        ]
        db.session.bulk_save_objects(default_services)

    # 3. Products Seed (Retail Inventory)
    if Product.query.count() == 0:
        default_products = [
            Product(sku="JC-POM-01", name="Matte Clay Pomade", description="Strong hold, natural matte finish for men's styling", wholesale_cost=7.50, retail_price=18.00, stock_qty=24, category="Hair Care"),
            Product(sku="JC-OIL-02", name="Argan Hair & Beard Serum", description="Nourishing shine and anti-frizz oil treatment", wholesale_cost=9.00, retail_price=22.00, stock_qty=18, category="Hair Care"),
            Product(sku="JC-SHP-03", name="Color Protect Shampoo 16oz", description="Sulfate-free salon formulation for dyed & highlighted hair", wholesale_cost=11.00, retail_price=26.00, stock_qty=12, category="Hair Care")
        ]
        db.session.bulk_save_objects(default_products)

    # 4. Overhead Expenses Seed
    if StudioExpense.query.count() == 0:
        default_expenses = [
            StudioExpense(title="Divine Salon Suite 105 Monthly Rent", category=ExpenseCategory.RENT, amount=950.00, vendor="Divine Salon Properties"),
            StudioExpense(title="Disinfectant & Sanitizing Supplies", category=ExpenseCategory.SUPPLIES, amount=65.00, vendor="Sally Beauty Supply"),
            StudioExpense(title="TikTok & Meta Local Ad Promotions", category=ExpenseCategory.MARKETING, amount=85.00, vendor="Meta Platforms")
        ]
        db.session.bulk_save_objects(default_expenses)
        
    db.session.commit()