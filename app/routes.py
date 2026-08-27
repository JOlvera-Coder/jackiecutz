from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import db
from app.models import User, Customer, BarberBooking
from werkzeug.security import generate_password_hash, check_password_hash
import re

main_bp = Blueprint('main', __name__)

def clean_phone(phone_str):
    if not phone_str:
        return ""
    return re.sub(r'\D', '', str(phone_str))

@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember_me'))

        digits = clean_phone(identifier)

        # Check Stylist / User first
        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session.permanent = remember
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('main.stylist_dashboard'))

        # Check Customer
        customer = Customer.query.filter(
            (Customer.email == identifier) | 
            (Customer.phone == digits) if digits else (Customer.email == identifier)
        ).first()

        if customer and customer.password_hash and check_password_hash(customer.password_hash, password):
            session['customer_id'] = customer.id
            session.permanent = remember
            flash(f"Welcome back, {customer.name}!", "success")
            return redirect(url_for('main.customer_portal'))

        flash("Invalid login credentials. Please try again.", "danger")
        return redirect(url_for('main.login'))

    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    form_data = {}
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else request.form.get('name', '').strip()
        
        phone_raw = request.form.get('phone', '')
        phone = clean_phone(phone_raw)
        email = request.form.get('email', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        address = request.form.get('address', '').strip()
        gender = request.form.get('gender', '').strip()
        birthday = request.form.get('birthday', '').strip()
        password = request.form.get('password', '').strip()
        notes = request.form.get('notes', '').strip()

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone_raw,
            'email': email,
            'zip_code': zip_code,
            'address': address,
            'gender': gender,
            'birthday': birthday,
            'notes': notes
        }

        # Specific field validation
        missing = []
        if not first_name and not full_name:
            missing.append("First Name")
        if not phone or len(phone) < 10:
            missing.append("Valid 10-digit Phone Number")
        if not password:
            missing.append("Password")
        if not zip_code:
            missing.append("Zip Code")

        if missing:
            flash(f"Please fill out required fields: {', '.join(missing)}.", "danger")
            return render_template('register.html', form_data=form_data)

        existing = Customer.query.filter(Customer.phone == phone).first()
        if existing:
            flash("An account with that phone number already exists. Please log in.", "warning")
            return redirect(url_for('main.login'))

        # Pack extra metadata into notes
        meta_parts = []
        if address:
            meta_parts.append(f"Address: {address}")
        if zip_code:
            meta_parts.append(f"Zip: {zip_code}")
        if gender:
            meta_parts.append(f"Gender: {gender}")
        if birthday:
            meta_parts.append(f"DOB: {birthday}")
        if notes:
            meta_parts.append(f"Notes: {notes}")
            
        full_notes = " | ".join(meta_parts)

        new_customer = Customer(
            name=full_name,
            phone=phone,
            email=email,
            password_hash=generate_password_hash(password),
            notes=full_notes
        )
        db.session.add(new_customer)
        db.session.commit()

        # Log customer in and route straight to portal
        session['customer_id'] = new_customer.id
        flash(f"Welcome to Jackiecutz, {first_name or full_name}! Your account has been created.", "success")
        return redirect(url_for('main.customer_portal'))

    return render_template('register.html', form_data=form_data)

@main_bp.route('/customer/portal')
def customer_portal():
    customer_id = session.get('customer_id')
    if not customer_id:
        flash("Please log in to access your profile.", "warning")
        return redirect(url_for('main.login'))

    customer = Customer.query.get(customer_id)
    if not customer:
        session.pop('customer_id', None)
        return redirect(url_for('main.login'))

    bookings = BarberBooking.query.filter_by(customer_id=customer.id).order_by(BarberBooking.start_time.desc()).all()
    return render_template('customer_portal.html', customer=customer, bookings=bookings)

@main_bp.route('/stylist/dashboard')
def stylist_dashboard():
    user_id = session.get('user_id')
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

@main_bp.route('/kiosk')
def kiosk():
    return render_template('kiosk.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash("Password reset instructions have been sent if an account matches.", "info")
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('main.login'))
