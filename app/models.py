from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, index=True, nullable=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    birthday = db.Column(db.String(30), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship('BarberBooking', backref='customer', lazy='dynamic')

class BarberService(db.Model):
    __tablename__ = 'barber_services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    category = db.Column(db.String(50), default="Haircut")
    duration_minutes = db.Column(db.Integer, default=30)

class BarberBooking(db.Model):
    __tablename__ = 'barber_bookings'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    service_name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(50), default="Confirmed")
    appointment_time = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, default=0.0)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50), default="Retail")

class ExpenseCategory(db.Model):
    __tablename__ = 'expense_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)

class StudioExpense(db.Model):
    __tablename__ = 'studio_expenses'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    description = db.Column(db.String(255), nullable=True)
    date = db.Column(db.Date, default=datetime.utcnow)