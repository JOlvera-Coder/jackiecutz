import os
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import (
    User, Customer, FamilyMember, BarberService, 
    BarberBooking, Product, ExpenseCategory, StudioExpense
)

# Alias for backwards compatibility across routes
Appointment = BarberBooking

main_bp = Blueprint('main', __name__)

DEFAULT_TIME_SLOTS = [
    "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
    "12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM",
    "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
    "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM",
    "06:00 PM", "06:30 PM"
]

@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))

        # Check Staff / Stylist User first
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            if hasattr(user, 'role') and user.role in ['stylist', 'admin', 'owner', 'barber']:
                return redirect(url_for('main.stylist_dashboard'))
            return redirect(url_for('main.customer_portal'))

        # Check Customer profile by Phone, Username, or Name
        customer = Customer.query.filter(
            (Customer.phone == identifier) | (Customer.username == identifier) | (Customer.name == identifier)
        ).first()

        if customer:
            session['customer_id'] = customer.id
            return redirect(url_for('main.customer_portal'))

        # If entering a new phone number, create quick client profile
        if identifier:
            new_cust = Customer(name=identifier, phone=identifier)
            db.session.add(new_cust)
            db.session.commit()
            session['customer_id'] = new_cust.id
            return redirect(url_for('main.customer_portal'))

        flash('Invalid credentials. Please verify your info.', 'danger')

    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.pop('customer_id', None)
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('main.login'))

@main_bp.route('/customer/portal')
def customer_portal():
    customer = None
    if current_user.is_authenticated:
        customer = Customer.query.filter_by(user_id=current_user.id).first() if hasattr(Customer, 'user_id') else None
    elif 'customer_id' in session:
        customer = Customer.query.get(session['customer_id'])

    services = BarberService.query.filter_by(is_active=True).all() if hasattr(BarberService, 'is_active') else BarberService.query.all()
    products = Product.query.filter_by(is_active=True).all() if hasattr(Product, 'is_active') else Product.query.all()
    
    user_bookings = []
    family_members = []
    if customer:
        if hasattr(BarberBooking, 'appointment_time'):
            user_bookings = BarberBooking.query.filter_by(customer_id=customer.id).order_by(BarberBooking.appointment_time.desc()).limit(10).all()
        elif hasattr(BarberBooking, 'date'):
            user_bookings = BarberBooking.query.filter_by(customer_id=customer.id).order_by(BarberBooking.date.desc()).limit(10).all()
        else:
            user_bookings = BarberBooking.query.filter_by(customer_id=customer.id).limit(10).all()
        
        family_members = FamilyMember.query.filter_by(customer_id=customer.id).all() if hasattr(FamilyMember, 'customer_id') else []

    return render_template(
        'booking.html',
        customer=customer,
        services=services,
        products=products,
        time_slots=DEFAULT_TIME_SLOTS,
        bookings=user_bookings,
        family_members=family_members
    )

@main_bp.route('/book', methods=['POST'])
def book_service():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    service_id = request.form.get('service_id')
    appointment_date = request.form.get('appointment_date')
    time_slot = request.form.get('time_slot')
    notes = request.form.get('notes', '')
    payment_method = request.form.get('payment_method', 'card_hold')

    if not name or not appointment_date or not time_slot:
        flash('Please fill all required booking details.', 'warning')
        return redirect(url_for('main.customer_portal'))

    customer = None
    if current_user.is_authenticated and hasattr(Customer, 'user_id'):
        customer = Customer.query.filter_by(user_id=current_user.id).first()
    elif 'customer_id' in session:
        customer = Customer.query.get(session['customer_id'])

    if not customer:
        customer = Customer.query.filter_by(phone=phone).first() if phone else None
        if not customer:
            customer = Customer(name=name, phone=phone)
            db.session.add(customer)
            db.session.commit()
        session['customer_id'] = customer.id

    service = BarberService.query.get(service_id)
    service_name = service.name if service else 'Studio Haircut'
    service_price = service.price if service else 25.0

    try:
        combined_dt_str = f"{appointment_date} {time_slot}"
        appointment_dt = datetime.strptime(combined_dt_str, "%Y-%m-%d %I:%M %p")
    except Exception:
        appointment_dt = datetime.now()

    appt = BarberBooking(
        customer_id=customer.id,
        service_id=service.id if service else None,
        service_name=service_name if hasattr(BarberBooking, 'service_name') else None,
        price=service_price if hasattr(BarberBooking, 'price') else None,
        appointment_time=appointment_dt if hasattr(BarberBooking, 'appointment_time') else None,
        status='Booked' if hasattr(BarberBooking, 'status') else None,
        payment_method=payment_method if hasattr(BarberBooking, 'payment_method') else None,
        notes=notes if hasattr(BarberBooking, 'notes') else None
    )
    db.session.add(appt)
    db.session.commit()

    flash('Your appointment has been successfully scheduled!', 'success')
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/stylist/dashboard')
def stylist_dashboard():
    appointments = BarberBooking.query.all()
    services = BarberService.query.all()
    return render_template(
        'stylist_dashboard.html' if os.path.exists('app/templates/stylist_dashboard.html') else 'booking.html',
        appointments=appointments,
        services=services
    )

@main_bp.route('/kiosk')
def kiosk():
    services = BarberService.query.all()
    return render_template('kiosk.html' if os.path.exists('app/templates/kiosk.html') else 'booking.html', services=services)

@main_bp.route('/api/available-slots')
def available_slots():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'slots': DEFAULT_TIME_SLOTS, 'is_closed': False})

    try:
        req_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        # Sunday=6, Monday=0
        if req_date.weekday() in [0, 6]:
            return jsonify({'slots': [], 'is_closed': True})
    except Exception:
        pass

    return jsonify({'slots': DEFAULT_TIME_SLOTS, 'is_closed': False})

@main_bp.route('/update_profile', methods=['POST'])
def update_profile():
    if 'customer_id' in session:
        cust = Customer.query.get(session['customer_id'])
        if cust:
            cust.name = request.form.get('name', cust.name)
            cust.email = request.form.get('email', cust.email)
            db.session.commit()
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/update_credentials', methods=['POST'])
def update_credentials():
    if 'customer_id' in session:
        cust = Customer.query.get(session['customer_id'])
        if cust:
            cust.phone = request.form.get('phone', cust.phone)
            cust.username = request.form.get('username', cust.username)
            db.session.commit()
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/add_family_member', methods=['POST'])
def add_family_member():
    if 'customer_id' in session:
        name = request.form.get('name')
        rel = request.form.get('relationship', 'Child')
        if name:
            fm = FamilyMember(customer_id=session['customer_id'], name=name, relationship=rel)
            db.session.add(fm)
            db.session.commit()
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/delete_family_member/<int:member_id>', methods=['POST'])
def delete_family_member(member_id):
    fm = FamilyMember.query.get(member_id)
    if fm:
        db.session.delete(fm)
        db.session.commit()
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/delete_account', methods=['POST'])
def delete_account():
    if 'customer_id' in session:
        cust = Customer.query.get(session['customer_id'])
        if cust:
            db.session.delete(cust)
            db.session.commit()
        session.pop('customer_id', None)
    return redirect(url_for('main.login'))