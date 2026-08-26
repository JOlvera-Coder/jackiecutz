from datetime import datetime, timedelta
import enum
import json
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class BookingStatus(enum.Enum):
    BOOKED = 'booked'
    WAITING = 'waiting'
    IN_CHAIR = 'in_chair'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class PaymentMethod(enum.Enum):
    CASH = 'cash'
    ZELLE = 'zelle'
    CASH_APP = 'cash_app'
    CARD = 'card'

class POStatus(enum.Enum):
    DRAFT = 'draft'
    PENDING = 'pending'
    RECEIVED = 'received'
    CLOSED = 'closed'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    birthday = db.Column(db.String(20), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    city = db.Column(db.String(80), nullable=True, default='Houston')
    acquisition_channel = db.Column(db.String(80), nullable=True)
    referred_by = db.Column(db.String(120), nullable=True)
    family_members_json = db.Column(db.Text, default='[]')
    specialties_json = db.Column(db.Text, default='[]')
    commission_rate = db.Column(db.Float, default=60.0) # 60% stylist / 40% house standard
    is_active_stylist = db.Column(db.Boolean, default=True)
    role = db.Column(db.String(20), default='client')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_family_members(self):
        try:
            return json.loads(self.family_members_json or '[]')
        except Exception:
            return []

    def set_family_members(self, members_list):
        self.family_members_json = json.dumps(members_list)

    def get_specialties(self):
        try:
            return json.loads(self.specialties_json or '[]')
        except Exception:
            return []

    def set_specialties(self, spec_list):
        self.specialties_json = json.dumps(spec_list)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    birthday = db.Column(db.String(20), nullable=True)
    zip_code = db.Column(db.String(10), nullable=True)
    city = db.Column(db.String(80), nullable=True, default='Houston')
    acquisition_channel = db.Column(db.String(80), nullable=True)
    referred_by = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('BarberBooking', backref='customer', lazy='dynamic', cascade='all, delete-orphan')

class BarberService(db.Model):
    __tablename__ = 'barber_services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default="Haircut")
    price = db.Column(db.Numeric(10, 2), nullable=False)
    duration_minutes = db.Column(db.Integer, default=20)
    is_active = db.Column(db.Boolean, default=True)

class BarberBooking(db.Model):
    __tablename__ = 'barber_bookings'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('barber_services.id'), nullable=False)
    stylist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    scheduled_time = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.BOOKED, nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=True)
    is_paid = db.Column(db.Boolean, default=False)
    final_amount = db.Column(db.Numeric(10, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    service = db.relationship('BarberService')
    stylist = db.relationship('User', backref='assigned_bookings')

# --- INVENTORY & PURCHASE ORDER ENGINE ---
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), default="Hair Care")
    wholesale_cost = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    retail_price = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    stock_qty = db.Column(db.Integer, default=0)
    low_stock_threshold = db.Column(db.Integer, default=5)
    image_url = db.Column(db.String(255), default="/static/img/card_bg.jpg")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    supplier_name = db.Column(db.String(120), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    total_cost = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum(POStatus), default=POStatus.PENDING)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    received_at = db.Column(db.DateTime, nullable=True)

    product = db.relationship('Product', backref='purchase_orders')

class ProductSale(db.Model):
    __tablename__ = 'product_sales'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    stylist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    sold_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product')
    stylist = db.relationship('User')
    customer = db.relationship('Customer')

# --- OVERHEAD EXPENSE & TAX LOGS ---
class ExpenseCategory(enum.Enum):
    RENT = 'rent'
    UTILITIES = 'utilities'
    SUPPLIES = 'supplies'
    EQUIPMENT = 'equipment'
    MARKETING = 'marketing'
    INSURANCE = 'insurance'
    OTHER = 'other'

class StudioExpense(db.Model):
    __tablename__ = 'studio_expenses'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.Enum(ExpenseCategory), default=ExpenseCategory.SUPPLIES)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    vendor = db.Column(db.String(120), nullable=True)
    expense_date = db.Column(db.Date, default=datetime.utcnow().date)
    notes = db.Column(db.Text, nullable=True)
    is_tax_deductible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
