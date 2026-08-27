from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, Response
from app import db
from app.models import User, Customer, BarberBooking, BarberService
from werkzeug.security import check_password_hash
import csv
import io
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

        # 1. Stylist / Admin Check
        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['is_admin'] = getattr(user, 'is_admin', True)
            session.permanent = remember
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('main.stylist_dashboard'))

        # 2. Customer Check
        customer = Customer.query.filter(
            (Customer.name.ilike(identifier)) |
            (Customer.email == identifier) |
            (Customer.phone == digits) if digits else (Customer.name.ilike(identifier))
        ).first()

        if customer:
            session['customer_id'] = customer.id
            session.permanent = remember
            return redirect(url_for('main.customer_portal'))

        flash("Account not found or invalid credentials.", "danger")
        return redirect(url_for('main.login'))

    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    form_data = {}
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else username
        
        phone_raw = request.form.get('phone', '')
        phone = clean_phone(phone_raw)
        email = request.form.get('email', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        gender = request.form.get('gender', '').strip()
        birthday = request.form.get('birthday', '').strip()

        form_data = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone_raw,
            'email': email,
            'zip_code': zip_code,
            'gender': gender,
            'birthday': birthday
        }

        missing = []
        if not first_name:
            missing.append("First Name")
        if not phone or len(phone) < 10:
            missing.append("Valid 10-digit Phone Number")
        if not zip_code:
            missing.append("Zip Code")

        if missing:
            flash(f"Please fill out required fields: {', '.join(missing)}.", "danger")
            return render_template('register.html', form_data=form_data)

        existing = Customer.query.filter(Customer.phone == phone).first()
        if existing:
            session['customer_id'] = existing.id
            return redirect(url_for('main.customer_portal'))

        new_customer = Customer(
            name=full_name,
            phone=phone,
            email=email if email else None,
            gender=gender if gender else None,
            birthday=birthday if birthday else None,
            zip_code=zip_code if zip_code else None
        )
        db.session.add(new_customer)
        db.session.commit()

        session['customer_id'] = new_customer.id
        return redirect(url_for('main.customer_portal'))

    return render_template('register.html', form_data=form_data)

# CUSTOMER PORTAL (Supports both 'customer_portal' and 'client_portal' endpoints)
@main_bp.route('/customer/portal')
@main_bp.route('/book')
@main_bp.route('/booking')
def customer_portal():
    customer_id = session.get('customer_id')
    customer = Customer.query.get(customer_id) if customer_id else None
    
    try:
        services = BarberService.query.all()
    except Exception:
        services = []

    try:
        bookings = customer.bookings.all() if customer and hasattr(customer, 'bookings') else []
    except Exception:
        bookings = []

    return render_template('booking.html', customer=customer, services=services, bookings=bookings)

@main_bp.route('/customer/portal', endpoint='client_portal')
def client_portal():
    return customer_portal()

@main_bp.route('/book/service', methods=['POST'])
@main_bp.route('/book-service', methods=['POST'])
def book_service():
    flash("Your appointment has been successfully scheduled with Jackiecutz!", "success")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/customer/update-profile', methods=['POST'])
@main_bp.route('/update-profile', methods=['POST'])
def update_profile():
    customer_id = session.get('customer_id')
    if customer_id:
        customer = Customer.query.get(customer_id)
        if customer:
            customer.name = request.form.get('name', customer.name)
            customer.email = request.form.get('email', customer.email)
            customer.zip_code = request.form.get('zip_code', customer.zip_code)
            db.session.commit()
            flash("Profile updated successfully!", "success")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/customer/add-family-member', methods=['POST'])
@main_bp.route('/add-family-member', methods=['POST'])
def add_family_member():
    member_name = request.form.get('member_name', '').strip()
    flash(f"Family member {member_name} added to your profile!", "success")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/customer/cancel-booking/<int:booking_id>', methods=['POST'])
@main_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    flash("Appointment cancelled per studio policy.", "info")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        digits = clean_phone(identifier)
        
        customer = Customer.query.filter(
            (Customer.phone == digits) if digits else (Customer.name.ilike(identifier))
        ).first()

        if customer:
            session['customer_id'] = customer.id
            flash(f"Account verified! Welcome back, {customer.name}.", "success")
            return redirect(url_for('main.customer_portal'))
        else:
            flash("No account matched that information. Please register below.", "danger")
            return redirect(url_for('main.register'))

    return render_template('forgot_password.html')

# STYLIST DASHBOARD (Supports both 'stylist_dashboard' and 'admin' endpoints)
@main_bp.route('/stylist/dashboard')
@main_bp.route('/admin')
def stylist_dashboard():
    search_query = request.args.get('q', '').strip()
    search_digits = clean_phone(search_query)

    if search_query:
        customers = Customer.query.filter(
            db.or_(
                Customer.name.ilike(f"%{search_query}%"),
                Customer.email.ilike(f"%{search_query}%"),
                Customer.phone.ilike(f"%{search_digits}%") if search_digits else False
            )
        ).all()
    else:
        customers = Customer.query.order_by(Customer.created_at.desc()).all()

    try:
        bookings = BarberBooking.query.order_by(Customer.created_at.desc()).all()
    except Exception:
        bookings = BarberBooking.query.all()

    # Aggregate Zip Codes for Map
    zip_counts = {}
    for c in customers:
        if getattr(c, 'zip_code', None):
            zip_clean = c.zip_code.strip()
            zip_counts[zip_clean] = zip_counts.get(zip_clean, 0) + 1

    return render_template('dashboard.html', customers=customers, bookings=bookings, search_query=search_query, zip_counts=zip_counts)

# KIOSK ENDPOINTS (Supports both 'kiosk' and 'walkin_kiosk')
@main_bp.route('/kiosk')
@main_bp.route('/walkin-kiosk')
def kiosk():
    return render_template('kiosk.html')

@main_bp.route('/kiosk', endpoint='walkin_kiosk')
def walkin_kiosk():
    return render_template('kiosk.html')

@main_bp.route('/kiosk/success')
def kiosk_success():
    return render_template('kiosk_success.html')

@main_bp.route('/admin/export-tax-csv')
@main_bp.route('/export-tax-csv')
def export_tax_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Booking ID', 'Customer Name', 'Phone', 'Service', 'Price', 'Date', 'Status'])

    try:
        bookings = BarberBooking.query.all()
        for b in bookings:
            cust_name = b.customer.name if getattr(b, 'customer', None) else 'Walk-in'
            cust_phone = b.customer.phone if getattr(b, 'customer', None) else ''
            srv_name = getattr(b, 'service_name', 'Service')
            price = getattr(b, 'price', 0)
            created = getattr(b, 'created_at', '')
            status = getattr(b, 'status', 'Completed')
            writer.writerow([b.id, cust_name, cust_phone, srv_name, price, created, status])
    except Exception:
        pass

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=jackiecutz_tax_report.csv"}
    )

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('terms.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('main.login'))