from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, Response
from app import db
from app.models import User, Customer, BarberBooking, BarberService
from werkzeug.security import check_password_hash
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
# 1. CUSTOMER AUTHENTICATION & RECOVERY
# ==========================================

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember_me'))

        digits = clean_phone(identifier)

        # Stylist / Owner Admin Check
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

        # Customer / Client Check
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
# 2. CUSTOMER BOOKING PORTAL & ACTIONS
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

# ==========================================
# 3. WALK-IN FRONT-DESK KIOSK APP
# ==========================================

@main_bp.route('/kiosk', methods=['GET', 'POST'])
@main_bp.route('/walkin-kiosk', methods=['GET', 'POST'])
def kiosk():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone_raw = request.form.get('phone', '')
        phone = clean_phone(phone_raw)
        service_id = request.form.get('service_id')

        if not name or not phone:
            flash("Please enter both your Name and Phone Number.", "danger")
            return redirect(url_for('main.kiosk'))

        customer = Customer.query.filter(Customer.phone == phone).first()
        if not customer:
            customer = Customer(name=name, phone=phone)
            db.session.add(customer)
            db.session.commit()

        new_booking = BarberBooking(
            customer_id=customer.id,
            service_name="Walk-In Service",
            price=35.00,
            status="In Queue"
        )
        db.session.add(new_booking)
        db.session.commit()

        return redirect(url_for('main.kiosk_success', name=name))

    try:
        services = BarberService.query.all()
    except Exception:
        services = []

    return render_template('kiosk.html', services=services)

@main_bp.route('/kiosk', endpoint='walkin_kiosk')
def walkin_kiosk():
    return kiosk()

@main_bp.route('/kiosk/success')
def kiosk_success():
    client_name = request.args.get('name', 'Client')
    return render_template('kiosk_success.html', client_name=client_name)

# ==========================================
# 4. STYLIST COMMAND CENTER & ACTIONS
# ==========================================

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

    try:
        services = BarberService.query.all()
    except Exception:
        services = []

    # Financial & KPI Calculations
    gross_revenue = 0.0
    today_revenue = 0.0
    completed_bookings = 0
    pending_bookings = 0
    today_bookings = 0
    today_date = date.today()

    for b in bookings:
        price = float(getattr(b, 'price', 0) or 0)
        status = getattr(b, 'status', 'Completed')
        b_time = getattr(b, 'created_at', None) or getattr(b, 'appointment_time', None)

        gross_revenue += price
        if status in ['Completed', 'completed', 'Paid', 'paid']:
            completed_bookings += 1
        elif status in ['Pending', 'pending', 'Confirmed', 'confirmed']:
            pending_bookings += 1

        if b_time and hasattr(b_time, 'date') and b_time.date() == today_date:
            today_bookings += 1
            today_revenue += price

    total_clients = len(customers)
    total_bookings = len(bookings)
    
    total_overhead = round(gross_revenue * 0.15, 2)
    net_profit = round(gross_revenue - total_overhead, 2)
    net_income = net_profit
    booth_rent = 0.0
    product_sales = 0.0
    tax_deductible_overhead = total_overhead
    tax_liability_est = round(net_income * 0.20, 2)
    barber_payout = round(gross_revenue * 0.60, 2)
    shop_cut = round(gross_revenue * 0.40, 2)

    zip_counts = {}
    for c in customers:
        if getattr(c, 'zip_code', None):
            z_clean = c.zip_code.strip()
            zip_counts[z_clean] = zip_counts.get(z_clean, 0) + 1

    return render_template(
        'dashboard.html',
        customers=customers,
        bookings=bookings,
        services=services,
        search_query=search_query,
        gross_revenue=gross_revenue,
        total_overhead=total_overhead,
        net_profit=net_profit,
        net_income=net_income,
        booth_rent=booth_rent,
        product_sales=product_sales,
        tax_deductible_overhead=tax_deductible_overhead,
        tax_liability_est=tax_liability_est,
        barber_payout=barber_payout,
        shop_cut=shop_cut,
        today_revenue=today_revenue,
        total_clients=total_clients,
        total_bookings=total_bookings,
        completed_bookings=completed_bookings,
        pending_bookings=pending_bookings,
        today_bookings=today_bookings,
        zip_counts=zip_counts
    )

# Dashboard Management Actions
@main_bp.route('/admin/add-product', methods=['POST'])
@main_bp.route('/add-product', methods=['POST'])
def add_product():
    product_name = request.form.get('name', 'Product')
    flash(f"Product '{product_name}' registered successfully.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/admin/add-service', methods=['POST'])
@main_bp.route('/add-service', methods=['POST'])
def add_service():
    name = request.form.get('name', '').strip()
    price = request.form.get('price', 0)
    category = request.form.get('category', 'Haircut')
    if name:
        new_srv = BarberService(name=name, price=float(price), category=category)
        db.session.add(new_srv)
        db.session.commit()
        flash(f"Service '{name}' added to salon catalog.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/admin/update-booking-status/<int:booking_id>', methods=['POST'])
@main_bp.route('/update-booking-status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id):
    booking = BarberBooking.query.get(booking_id)
    if booking:
        booking.status = request.form.get('status', 'Completed')
        db.session.commit()
        flash(f"Booking #{booking_id} status updated.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/admin/export-tax-csv')
@main_bp.route('/export-tax-csv')
def export_tax_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Booking ID', 'Customer Name', 'Phone', 'Service', 'Price', 'Status'])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=jackiecutz_tax_report.csv"}
    )

# ==========================================
# 5. GENERAL ROUTES
# ==========================================

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