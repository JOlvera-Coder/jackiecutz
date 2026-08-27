import re
from datetime import datetime, date, time, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.models import (
    Customer, BarberService, BarberBooking, BookingStatus,
    User, Product, PurchaseOrder, ProductSale, StudioExpense
)

main_bp = Blueprint('main', __name__)

def clean_phone(phone_str):
    return re.sub(r'\D', '', phone_str or '')

@main_bp.route('/')
def index():
    services = BarberService.query.filter_by(is_active=True).all()
    return render_template('index.html', services=services)

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        gender = request.form.get('gender', '').strip()
        birthday = request.form.get('birthday', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        address = request.form.get('address', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        missing = []
        if not first_name: missing.append("First Name")
        if not last_name: missing.append("Last Name")
        if not gender: missing.append("Gender")
        if not birthday: missing.append("Birthday")
        if not email: missing.append("Email Address")
        if not phone: missing.append("Phone Number")
        if not zip_code: missing.append("Zip Code")
        if not username: missing.append("Username")
        if not password: missing.append("Password")

        if missing:
            flash(f"Please fill out: {', '.join(missing)}", "error")
            return render_template('register.html', form_data=request.form)

        cleaned = clean_phone(phone)
        existing_customer = Customer.query.filter(
            (Customer.phone == cleaned) | (Customer.email == email)
        ).first()

        if existing_customer:
            flash("An account with this phone number or email already exists. Please log in.", "error")
            return render_template('register.html', form_data=request.form)

        notes_detail = f"Zip: {zip_code}"
        if address:
            notes_detail += f" | Address: {address}"
        notes_detail += f" | Username: {username}"

        new_customer = Customer(
            name=full_name,
            phone=cleaned,
            email=email,
            gender=gender,
            birthday=birthday,
            notes=notes_detail
        )
        db.session.add(new_customer)
        db.session.commit()

        session['customer_id'] = new_customer.id
        session['customer_name'] = new_customer.name
        session['customer_phone'] = new_customer.phone

        flash(f"Welcome, {first_name}! Your account has been created.", "success")
        return redirect(url_for('main.index'))

    return render_template('register.html', form_data={})

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        cleaned = clean_phone(identifier)
        customer = Customer.query.filter(
            (Customer.phone == cleaned) | (Customer.email == identifier) | (Customer.notes.ilike(f"%Username: {identifier}%"))
        ).first()
        
        if customer:
            session['customer_id'] = customer.id
            session['customer_name'] = customer.name
            session['customer_phone'] = customer.phone
            flash(f"Welcome back, {customer.name}!", "success")
            return redirect(url_for('main.index'))
        else:
            flash("Account not found. Please register.", "error")
            return render_template('login.html')
            
    return render_template('login.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for('main.index'))

@main_bp.route('/book', methods=['GET', 'POST'])
def book():
    services = BarberService.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        customer_id = session.get('customer_id')
        name = request.form.get('name')
        phone = clean_phone(request.form.get('phone'))
        service_id = request.form.get('service_id')
        booking_date_str = request.form.get('booking_date')
        booking_time_str = request.form.get('booking_time')

        if not customer_id:
            customer = Customer.query.filter_by(phone=phone).first()
            if not customer:
                customer = Customer(name=name, phone=phone)
                db.session.add(customer)
                db.session.commit()
            customer_id = customer.id

        booking_dt = datetime.strptime(f"{booking_date_str} {booking_time_str}", "%Y-%m-%d %H:%M")
        service = BarberService.query.get(service_id)

        new_booking = BarberBooking(
            customer_id=customer_id,
            service_id=service_id,
            start_time=booking_dt,
            end_time=booking_dt + timedelta(minutes=service.duration_minutes if service else 30),
            status=BookingStatus.CONFIRMED,
            total_price=service.price if service else 0.0
        )
        db.session.add(new_booking)
        db.session.commit()
        flash("Appointment booked successfully!", "success")
        return redirect(url_for('main.index'))

    return render_template('book.html', services=services)

@main_bp.route('/admin/dashboard')
def admin_dashboard():
    search_query = request.args.get('q', '').strip()
    search_digits = clean_phone(search_query)

    if search_query:
        customers = Customer.query.filter(
            db.or_(
                Customer.name.ilike(f"%{search_query}%"),
                Customer.email.ilike(f"%{search_query}%"),
                Customer.notes.ilike(f"%{search_query}%"),
                Customer.phone.ilike(f"%{search_digits}%") if search_digits else False
            )
        ).all()
    else:
        customers = Customer.query.order_by(Customer.created_at.desc()).all()

    bookings = BarberBooking.query.order_by(BarberBooking.start_time.desc()).all()
    return render_template('admin_dashboard.html', customers=customers, bookings=bookings, search_query=search_query)

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash("Password reset instructions have been sent if an account matches.", "info")
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')