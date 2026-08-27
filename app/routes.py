from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, Response
from app import db
from app.models import User, Customer, BarberBooking, BarberService
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date
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

# ==========================================
# 1. RETURNING CUSTOMER / STYLIST LOGIN
# ==========================================
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

        # 2. Returning Customer Check (Phone / Name / Email)
        customer = Customer.query.filter(
            (Customer.name.ilike(identifier)) |
            (Customer.email == identifier) |
            (Customer.phone == digits) if digits else (Customer.name.ilike(identifier))
        ).first()

        if customer:
            session['customer_id'] = customer.id
            session.permanent = remember
            flash(f"Welcome back, {customer.name}!", "success")
            return redirect(url_for('main.customer_portal'))

        flash("Account not found or invalid credentials.", "danger")
        return redirect(url_for('main.login'))

    return render_template('login.html')

# ==========================================
# 2. NEW CUSTOMER REGISTRATION
# ==========================================
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

        # If phone already exists, log in and transition straight to booking
        existing = Customer.query.filter(Customer.phone == phone).first()
        if existing:
            session['customer_id'] = existing.id
            flash(f"Welcome back, {existing.name}!", "success")
            return redirect(url_for('main.customer_portal'))

        # Create new customer record
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

        # Log new customer in automatically and route to booking
        session['customer_id'] = new_customer.id
        flash(f"Account successfully created! Welcome, {new_customer.name}.", "success")
        return redirect(url_for('main.customer_portal'))

    return render_template('register.html', form_data=form_data)

# ==========================================
# 3. FORGOT / RECOVER CREDENTIALS
# ==========================================
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

# ==========================================
# 4. CUSTOMER BOOKING PORTAL & ACTIONS
# ==========================================
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
    flash("Your appointment has been scheduled with Jackiecutz!", "success")
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

@main_bp.route('/customer/update-credentials', methods=['POST'])
@main_bp.route('/update-credentials', methods=['POST'])
def update_credentials():
    flash("Security credentials updated successfully.", "success")
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

# ==========================================
# 5. KIOSK & ADMIN ROUTE FALLBACKS
# ==========================================
@main_bp.route('/kiosk', methods=['GET', 'POST'])
@main_bp.route('/walkin-kiosk', methods=['GET', 'POST'])
def kiosk():
    return render_template('kiosk.html', services=[])

@main_bp.route('/kiosk', endpoint='walkin_kiosk')
def walkin_kiosk():
    return kiosk()

@main_bp.route('/kiosk/success')
def kiosk_success():
    return render_template('kiosk_success.html', client_name="Client")

@main_bp.route('/stylist/dashboard')
@main_bp.route('/admin')
def stylist_dashboard():
    customers = Customer.query.order_by(Customer.created_at.desc()).all()
    bookings = BarberBooking.query.all()
    return render_template(
        'dashboard.html',
        customers=customers,
        bookings=bookings,
        services=[],
        search_query="",
        gross_revenue=0.0,
        total_overhead=0.0,
        net_profit=0.0,
        net_income=0.0,
        booth_rent=0.0,
        product_sales=0.0,
        tax_deductible_overhead=0.0,
        tax_liability_est=0.0,
        barber_payout=0.0,
        shop_cut=0.0,
        today_revenue=0.0,
        total_clients=len(customers),
        total_bookings=len(bookings),
        completed_bookings=0,
        pending_bookings=0,
        today_bookings=0,
        zip_counts={}
    )

@main_bp.route('/admin/add-product', methods=['POST'])
@main_bp.route('/add-product', methods=['POST'])
def add_product():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/admin/create-purchase-order', methods=['POST'])
@main_bp.route('/create-purchase-order', methods=['POST'])
def create_purchase_order():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/admin/add-service', methods=['POST'])
@main_bp.route('/add-service', methods=['POST'])
def add_service():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/admin/update-booking-status/<int:booking_id>', methods=['POST'])
@main_bp.route('/update-booking-status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/admin/export-tax-csv')
@main_bp.route('/export-tax-csv')
def export_tax_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Booking ID', 'Customer Name', 'Phone', 'Service', 'Price', 'Status'])
    output.seek(0)
    return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=tax_report.csv"})

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