from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='client') # 'client' or 'stylist'

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    client_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    status = db.Column(db.String(30), default='waiting') # 'waiting', 'checked_in', 'in_chair', 'completed'
    payment_status = db.Column(db.String(30), default='in_app') # 'in_app' or 'cash'
    date = db.Column(db.Date)
    time = db.Column(db.String(20))

    service = db.relationship('Service', backref='appointments', lazy=True)
    user = db.relationship('User', backref='appointments', lazy=True)