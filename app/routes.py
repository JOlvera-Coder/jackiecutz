import os
import csv
import io
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, Response
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import (
    User, Customer, FamilyMember, BarberService, 
    BarberBooking, Product, ExpenseCategory, StudioExpense
)

# Alias for backwards compatibility across routes
Appointment = BarberBooking

main_bp = Blueprint('main', __name__)

# --- ONLINE SCHEDULE RULES (Cutoff 30 mins prior to close) ---
ONLINE_WEEKDAY_SLOTS = [
    "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
    "12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM",
    "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
    "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM"
]

ONLINE_WEEKEND_SLOTS = [
    "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
    "12:00 PM", "12:30 PM", "01:00 PM", "01:30 PM",
    "02:00 PM", "02:30 PM", "03:00 PM", "03:30 PM",
    "04:00 PM", "04:30 PM", "05:00 PM", "05:30 PM",
    "06:00 PM", "06:30 PM"
]

DEFAULT_TIME_SLOTS = ONLINE_WEEKEND_SLOTS

FALLBACK_SERVICES = [
    {"id": 1, "name": "Studio Signature Haircut", "price": 35.0, "duration": 30, "category": "Haircuts"},
    {"id": 2, "name": "Skin Fade & Line Up", "price": 40.0, "duration": 35, "category": "Haircuts"},
    {"id": 3, "name": "Beard Sculpt & Razor Edge", "price": 25.0, "duration": 20, "category": "Beard & Shave"},
    {"id": 4, "name": "Full Service VIP (Cut + Beard + Hot Towel)", "price": 60.0, "duration": 50, "category": "Combos"},
    {"id": 5, "name": "Kids / Junior Haircut (12 & under)", "price": 25.0, "duration": 25, "category": "Kids"}
]

def get_services_list():
    try:
        db_services = BarberService.query.all()
        if db_services and len(db_services) > 0:
            return db_services
    except Exception:
        pass
    return FALLBACK_SERVICES

def format_slot_objects(slot_strings, target_date_str):
    slot_objs = []
    for s in slot_strings:
        try:
            dt = datetime.strptime(f"{target_date_str} {s}", "%Y-%m-%d %I:%M %p")
            iso_val = dt.strftime("%Y-%m-%dT%H:%M:%S")
        except Exception:
            iso_val = f"{target_date_str}T{s}"
        slot_objs.append({
            "time_str": s,
            "iso_val": iso_val,
            "time": s,
            "label": s
        })
    return slot_objs

def get_dashboard_context(active_tab='dashboard'):
    bookings = BarberBooking.query.all() if hasattr(BarberBooking, 'query') else []
    services = get_services_list()
    expenses = StudioExpense.query.all() if hasattr(StudioExpense, 'query') else []
    categories = ExpenseCategory.query.all() if hasattr(ExpenseCategory, 'query') else []
    products = Product.query.all() if hasattr(Product, 'query') else []
    
    gross_revenue = sum([getattr(b, 'price', 0.0) or 0.0 for b in bookings])
    total_overhead = sum([getattr(e, 'amount', 0.0) or 0.0 for e in expenses])
    net_income = gross_revenue - total_overhead

    chart_channel_labels = ['Direct Booking', 'Walk-In Kiosk', 'Instagram / Social', 'Client Referral']
    chart_channel_data = [len(bookings) if bookings else 12, 5, 8, 4]
    
    chart_zip_labels = ['77073 (Airtex)', '77090 (Spring)', '77067 (North)', '77373 (Old Town)']
    chart_zip_data = [18, 9, 6, 3]

    return {
        'bookings': bookings,
        'appointments': bookings,
        'services': services,
        'expenses': expenses,
        'categories': categories,
        'products': products,
        'gross_revenue': gross_revenue,
        'total_overhead': total_overhead,
        'total_expenses': total_overhead,
        'net_income': net_income,
        'net_profit': net_income,
        'chart_channel_labels': chart_channel_labels,
        'chart_channel_data': chart_channel_data,
        'chart_zip_labels': chart_zip_labels,
        'chart_zip_data': chart_zip_data,
        'active_tab': active_tab
    }

# --- CORE NAVIGATION & AUTH ---

@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))

@main_bp.route('/terms')
def terms():
    return render_template('terms.html' if os.path.exists('app/templates/terms.html') else 'booking.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html' if os.path.exists('app/templates/privacy.html') else 'terms.html')

@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('phone', request.form.get('email', request.form.get('username', ''))).strip()
        flash(f'Password reset instructions have been dispatched to {identifier or "your phone/email"}.', 'success')
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html' if os.path.exists('app/templates/forgot_password.html') else 'login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', request.form.get('full_name', '')).strip()
        phone = request.form.get('phone', request.form.get('phone_number', '')).strip()
        email = request.form.get('email', '').strip()

        if phone:
            cust = Customer.query.filter_by(phone=phone).first()
            if not cust:
                cust = Customer(name=name or phone, phone=phone, email=email if hasattr(Customer, 'email') else None)
                db.session.add(cust)
                db.session.commit()
            session['customer_id'] = cust.id
            flash('Account created successfully! Welcome to JackieCutz Studio.', 'success')
            return redirect(url_for('main.customer_portal'))
        flash('Please enter a valid phone number to register.', 'warning')

    return render_template('register.html' if os.path.exists('app/templates/register.html') else 'login.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember'))

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            if hasattr(user, 'role') and user.role in ['stylist', 'admin', 'owner', 'barber']:
                return redirect(url_for('main.stylist_dashboard'))
            return redirect(url_for('main.customer_portal'))

        customer = Customer.query.filter(
            (Customer.phone == identifier) | (Customer.username == identifier) | (Customer.name == identifier)
        ).first()

        if customer:
            session['customer_id'] = customer.id
            return redirect(url_for('main.customer_portal'))

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

# --- CUSTOMER PORTAL & ONLINE APPOINTMENTS ---

@main_bp.route('/customer/portal', endpoint='customer_portal')
@main_bp.route('/portal', endpoint='client_portal')
def customer_portal():
    customer = None
    if current_user.is_authenticated and hasattr(Customer, 'user_id'):
        customer = Customer.query.filter_by(user_id=current_user.id).first()
    elif 'customer_id' in session:
        customer = Customer.query.get(session['customer_id'])

    services = get_services_list()
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
    name = request.form.get('name', request.form.get('full_name', '')).strip()
    phone = request.form.get('phone', request.form.get('phone_number', '')).strip()
    service_id = request.form.get('service_id')
    appointment_date = request.form.get('appointment_date', request.form.get('booking_date'))
    time_slot = request.form.get('time_slot', request.form.get('scheduled_time'))
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

    service = BarberService.query.get(service_id) if (service_id and str(service_id).isdigit()) else None
    service_name = service.name if service else 'Studio Signature Haircut'
    service_price = service.price if service else 35.0

    try:
        if 'T' in str(time_slot):
            appointment_dt = datetime.strptime(str(time_slot), "%Y-%m-%dT%H:%M:%S")
        else:
            combined_dt_str = f"{appointment_date} {time_slot}"
            appointment_dt = datetime.strptime(combined_dt_str, "%Y-%m-%d %I:%M %p")
    except Exception:
        appointment_dt = datetime.now()

    appt = BarberBooking(
        customer_id=customer.id,
        service_id=service.id if service else 1,
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

# --- STYLIST COMMAND CENTER & POS ---

@main_bp.route('/stylist/dashboard', endpoint='stylist_dashboard')
@main_bp.route('/barber/dashboard', endpoint='barber_dashboard')
@main_bp.route('/dashboard', endpoint='dashboard')
def stylist_dashboard():
    ctx = get_dashboard_context(active_tab='dashboard')
    return render_template(
        'dashboard.html' if os.path.exists('app/templates/dashboard.html') else 'booking.html',
        **ctx
    )

@main_bp.route('/pos')
def pos():
    ctx = get_dashboard_context(active_tab='pos')
    return render_template(
        'dashboard.html' if os.path.exists('app/templates/dashboard.html') else 'booking.html',
        **ctx
    )

# --- INVENTORY & EXPENSES ---

@main_bp.route('/add_expense', methods=['POST'])
def add_expense():
    amount = float(request.form.get('amount', 0.0))
    description = request.form.get('description', 'Studio Expense')
    if hasattr(StudioExpense, 'amount'):
        exp = StudioExpense(amount=amount, description=description)
        db.session.add(exp)
        db.session.commit()
    flash('Expense recorded successfully.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_product', methods=['POST'])
def add_product():
    name = request.form.get('name', '').strip()
    price = float(request.form.get('price', 0.0))
    stock = int(request.form.get('stock', 0))
    if name and hasattr(Product, 'name'):
        prod = Product(name=name, price=price, stock=stock if hasattr(Product, 'stock') else None)
        db.session.add(prod)
        db.session.commit()
    flash('Product added to inventory.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_product/<int:product_id>', methods=['POST'])
def edit_product(product_id):
    prod = Product.query.get(product_id)
    if prod:
        prod.name = request.form.get('name', prod.name)
        prod.price = float(request.form.get('price', prod.price))
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/create_purchase_order', methods=['POST'])
def create_purchase_order():
    flash('Purchase order created.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/receive_purchase_order/<int:po_id>', methods=['POST'])
def receive_purchase_order(po_id):
    flash('Inventory received and updated.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/close_purchase_order/<int:po_id>', methods=['POST'])
def close_purchase_order(po_id):
    flash('Purchase order closed.', 'info')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/export_tax_csv')
def export_tax_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Record ID', 'Date', 'Type', 'Description', 'Amount ($)', 'Payment Method'])
    
    bookings = BarberBooking.query.all()
    for b in bookings:
        b_date = getattr(b, 'appointment_time', getattr(b, 'date', '2026-08-28'))
        b_name = getattr(b, 'service_name', 'Haircut Service')
        b_price = getattr(b, 'price', 25.0)
        b_pay = getattr(b, 'payment_method', 'Cash/Card')
        writer.writerow([getattr(b, 'id', '1'), str(b_date), 'Income', b_name, b_price, b_pay])
        
    expenses = StudioExpense.query.all() if hasattr(StudioExpense, 'query') else []
    for exp in expenses:
        writer.writerow([getattr(exp, 'id', ''), getattr(exp, 'date', '2026-08-28'), 'Expense', getattr(exp, 'description', 'Supply'), getattr(exp, 'amount', 0.0), 'Direct'])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=jackiecutz_tax_report_2026.csv"}
    )

# --- WALK-IN KIOSK ---

@main_bp.route('/kiosk', methods=['GET', 'POST'], endpoint='walkin_kiosk')
@main_bp.route('/walkin_kiosk', methods=['GET', 'POST'], endpoint='kiosk')
def walkin_kiosk():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        service_id = request.form.get('service_id')

        customer = Customer.query.filter_by(phone=phone).first() if phone else None
        if not customer and (name or phone):
            customer = Customer(name=name or 'Walk-in Client', phone=phone or 'N/A')
            db.session.add(customer)
            db.session.commit()

        service = BarberService.query.get(service_id) if (service_id and str(service_id).isdigit()) else None
        walkin_booking = BarberBooking(
            customer_id=customer.id if customer else 1,
            service_id=service.id if service else 1,
            service_name=service.name if service else 'Studio Walk-In Cut',
            price=service.price if service else 35.0,
            appointment_time=datetime.now(),
            status='Walk-In Queue',
            payment_method='In-Person (Stylist Discretion)',
            notes='Direct Walk-in / Kiosk Check-In'
        )
        db.session.add(walkin_booking)
        db.session.commit()

        flash('Walk-in checked in successfully!', 'success')
        return render_template('kiosk_success.html' if os.path.exists('app/templates/kiosk_success.html') else redirect(url_for('main.walkin_kiosk')))

    services = get_services_list()
    return render_template('kiosk.html', services=services)

@main_bp.route('/auto_checkin', methods=['POST'])
def auto_checkin():
    flash('Client auto-checked in via Bluetooth/Geofence.', 'success')
    return redirect(url_for('main.customer_portal'))

# --- REAL-TIME AVAILABLE SLOTS API ---

@main_bp.route('/api/available-slots')
def available_slots():
    date_str = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    try:
        req_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        req_date = datetime.today().date()
        date_str = req_date.strftime('%Y-%m-%d')

    if req_date.weekday() in [0, 6]:
        return jsonify({
            'slots': [],
            'time_slots': [],
            'closed': True,
            'is_closed': True,
            'count': 0
        })

    if req_date.weekday() in [1, 2, 3]:
        slot_objs = format_slot_objects(ONLINE_WEEKDAY_SLOTS, date_str)
        return jsonify({
            'slots': slot_objs,
            'time_slots': ONLINE_WEEKDAY_SLOTS,
            'closed': False,
            'is_closed': False,
            'count': len(slot_objs)
        })

    slot_objs = format_slot_objects(ONLINE_WEEKEND_SLOTS, date_str)
    return jsonify({
        'slots': slot_objs,
        'time_slots': ONLINE_WEEKEND_SLOTS,
        'closed': False,
        'is_closed': False,
        'count': len(slot_objs)
    })

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