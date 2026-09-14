models_code = """from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), index=True)
    zip_code = db.Column(db.String(10), default='77073')
    city = db.Column(db.String(50), default='Houston')
    password_hash = db.Column(db.String(128))
    source_channel = db.Column(db.String(50), default='App')
    is_stylist = db.Column(db.Boolean, default=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    location_id = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    bookings = db.relationship('Booking', backref='client', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    stylist_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=True)
    service_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    retail_add_on = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(30), default='completed')
    source_channel = db.Column(db.String(50), default='App')
    payment_method = db.Column(db.String(50), default='Card')
    rebooked_on_checkout = db.Column(db.Boolean, default=False)
    duration_minutes = db.Column(db.Integer, default=45)
    service_notes = db.Column(db.String(255), default='')
    location_id = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), default='Stylist')
    specialties = db.Column(db.String(255), default='General')
    pay_type = db.Column(db.String(50), default='Commission')
    pay_rate = db.Column(db.Float, default=70.0)
    booth_rent = db.Column(db.Float, default=0.0)
    cashout_frequency = db.Column(db.String(30), default='Weekly')
    last_payout_date = db.Column(db.DateTime, default=datetime.utcnow)
    location_id = db.Column(db.Integer, default=1)
    
    bookings = db.relationship('Booking', backref='assigned_staff', lazy=True)

class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bank_name = db.Column(db.String(100), default='Not Connected')
    account_holder = db.Column(db.String(100), default='Unlinked Account')
    routing_number = db.Column(db.String(50), default='*****')
    account_number = db.Column(db.String(50), default='*****')
    account_type = db.Column(db.String(50), default='Checking')
    status = db.Column(db.String(50), default='Action Required: Unlinked ⚠️')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class ServiceCatalog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price_min = db.Column(db.Float, nullable=False)
    price_max = db.Column(db.Float, nullable=True)
    required_role = db.Column(db.String(50), default='Any')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, default=0)
    location_id = db.Column(db.Integer, default=1)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    location_id = db.Column(db.Integer, default=1)
"""

with open('app/models.py', 'w', encoding='utf-8') as f:
    f.write(models_code)

print("Successfully wrote full schema including BankAccount model to app/models.py!")