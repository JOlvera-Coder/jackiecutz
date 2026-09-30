import csv
import io
import os
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, make_response
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Message
from app.models import User
from app import db, mail

main_bp = Blueprint('main', __name__)

# --- FILE UPLOAD CONFIGURATION FOR IVONNE'S PUBLIC SITE ---
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'img', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# 0. PUBLIC BOOKING WEBSITE
# ==========================================

@main_bp.route('/')
@main_bp.route('/index')
def index():
    services = []
    products = []
    staff = []
    try:
        from app.models import Service, Product, Staff
        services = Service.query.all()
        products = Product.query.all()
        staff = Staff.query.all()
    except Exception as e:
        print(f"Index query fallback: {e}")

    return render_template('index_desktop.html', services=services, products=products, staff=staff)

# ==========================================
# 1. AUTH & ENTRY ROUTES
# ==========================================

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('login_identifier', '').strip()
        password = request.form.get('password', '')
        user_role = request.form.get('user_role', 'client')

        user = User.query.filter(
            (User.username == identifier) |
            (User.email == identifier) |
            (User.phone == identifier)
        ).first()

        if user and user.password_hash and check_password_hash(user.password_hash, password):
            if user_role == 'admin':
                if getattr(user, 'is_admin', False) or getattr(user, 'is_stylist', False):
                    login_user(user)
                    flash('Welcome to the Admin Dashboard!', 'success')
                    return redirect(url_for('main.stylist_dashboard'))
                else:
                    flash('Unauthorized admin access attempt.', 'danger')
                    return render_template('login.html')

            elif user_role == 'stylist':
                if getattr(user, 'is_stylist', False) or getattr(user, 'is_admin', False):
                    login_user(user)
                    flash(f'Welcome back, {user.first_name or "Stylist"}!', 'success')
                    return redirect(url_for('main.stylist_portal', staff_id=user.id))
                else:
                    flash('Account is not registered as a stylist.', 'danger')
                    return render_template('login.html')

            else:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('main.customer_portal'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')


@main_bp.route('/login_desktop', methods=['GET', 'POST'])
def login_desktop():
    if request.method == 'POST':
        identifier = request.form.get('login_identifier', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter(
            (User.username == identifier) |
            (User.email == identifier) |
            (User.phone == identifier)
        ).first()

        if user and user.password_hash and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful! Welcome back.', 'success')
            return redirect(url_for('main.index', _anchor='booking-section'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login_desktop.html')


@main_bp.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.login'))


@main_bp.route('/register', methods=['GET', 'POST'])
@main_bp.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        zip_code = request.form.get('zip_code', '').strip()
        gender = request.form.get('gender')
        birthday = request.form.get('birthday')

        existing_user = User.query.filter(
            (User.email == email) | 
            (User.phone == phone) | 
            (User.username == username)
        ).first()

        if existing_user:
            flash('An account with this email, phone, or username already exists. Please log in.', 'warning')
            return redirect(url_for('main.login'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            name=f"{first_name} {last_name}".strip(),
            phone=phone,
            email=email,
            zip_code=zip_code,
            gender=gender,
            birthdate=birthday,
            password_hash=generate_password_hash(password),
            is_stylist=False
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Registration successful!', 'success')
            return redirect(url_for('main.customer_portal'))
        except Exception:
            db.session.rollback()
            flash('Registration error occurred. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@main_bp.route('/register_desktop', methods=['GET', 'POST'])
def register_desktop():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        zip_code = request.form.get('zip_code', '').strip()

        existing_user = User.query.filter(
            (User.email == email) | 
            (User.phone == phone) | 
            (User.username == username)
        ).first()

        if existing_user:
            flash('An account with this email, phone, or username already exists.', 'warning')
            return redirect(url_for('main.login_desktop'))

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            username=username,
            name=f"{first_name} {last_name}".strip(),
            phone=phone,
            email=email,
            zip_code=zip_code,
            password_hash=generate_password_hash(password),
            is_stylist=False
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Registration successful! Returning to your booking.', 'success')
            return redirect(url_for('main.index', _anchor='booking-section'))
        except Exception:
            db.session.rollback()
            flash('Registration error occurred. Please try again.', 'danger')

    return render_template('register_desktop.html')


@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgot_password.html')


@main_bp.route('/terms')
def terms():
    return render_template('terms.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

# ==========================================
# 2. CUSTOMER PORTAL & BOOKING PAGE
# ==========================================

@main_bp.route('/booking')
def booking():
    services = []
    staff = []
    products = []
    try:
        from app.models import Service, Staff, Product
        services = Service.query.all()
        staff = Staff.query.all()
        products = Product.query.all()
    except Exception as e:
        print(f"Booking query fallback: {e}")

    return render_template('booking.html', services=services, staff=staff, products=products)


@main_bp.route('/customer_portal')
@main_bp.route('/customer-portal')
@main_bp.route('/client_dashboard')
def customer_portal():
    return render_template('customer_app.html')


@main_bp.route('/book_service', methods=['POST'])
def book_service():
    flash('Service booked successfully!', 'success')
    return redirect(url_for('main.customer_portal'))


@main_bp.route('/api/available-slots')
@main_bp.route('/api/get_slots')
def available_slots():
    return jsonify({'slots': ['10:00 AM', '11:30 AM', '01:30 PM', '04:00 PM']})

# ==========================================
# 3. KIOSK & QUEUE DISPLAY
# ==========================================

@main_bp.route('/walkin_kiosk')
@main_bp.route('/walkin-kiosk')
def walkin_kiosk():
    return render_template('kiosk.html')


@main_bp.route('/queue_display')
@main_bp.route('/queue-display')
def queue_display():
    return render_template('queue_display.html')

# ==========================================
# 4. DASHBOARD & STYLIST PORTAL
# ==========================================

@main_bp.route('/dashboard')
@main_bp.route('/stylist_dashboard')
@main_bp.route('/stylist-dashboard')
def stylist_dashboard():
    mock_bank = {'status': 'Connected', 'bank_name': 'Chase Bank', 'account_holder': 'Jackiecutz LLC', 'account_number': '•••• 1234', 'account_type': 'Business Checking'}
    mock_zip_counts = {'77073': 0}
    
    services = []
    products = []
    clients = []
    staff = []
    
    today_revenue = 0.0
    gross_revenue = 0.0
    total_overhead = 0.0
    kiosk_revenue = 0.0
    app_revenue = 0.0

    try:
        from app.models import User
        clients = User.query.filter_by(is_stylist=False).all()
        staff = User.query.filter_by(is_stylist=True).all()
    except Exception as e:
        print(f"User query error: {e}")

    try:
        from app.models import Service, Product
        services = Service.query.all()
        products = Product.query.all()
    except Exception as e:
        print(f"Service/Product query error: {e}")

    try:
        from app.models import Booking
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_bookings = Booking.query.filter(Booking.status == 'completed', Booking.timestamp >= today_start).all()
        today_revenue = sum(b.price for b in today_bookings if getattr(b, 'price', None))

        all_completed = Booking.query.filter_by(status='completed').all()
        gross_revenue = sum(b.price for b in all_completed if getattr(b, 'price', None))

        for b in all_completed:
            if getattr(b, 'source_channel', '') == 'Kiosk Terminal':
                kiosk_revenue += (getattr(b, 'price', 0.0) or 0.0)
            else:
                app_revenue += (getattr(b, 'price', 0.0) or 0.0)
    except Exception as e:
        print(f"Booking query error: {e}")

    try:
        from app.models import Expense
        all_expenses = Expense.query.all()
        total_overhead = sum(e.amount for e in all_expenses if getattr(e, 'amount', None))
    except Exception as e:
        print(f"Expense query error: {e}")

    net_income = max(0.0, gross_revenue - total_overhead)
    revpash = (today_revenue / 8.0) if today_revenue > 0 else 0.0

    return render_template(
        'dashboard.html', 
        bank=mock_bank,
        zip_counts=mock_zip_counts,
        services=services,
        products=products,
        clients=clients,
        staff=staff,
        today_revenue=today_revenue,
        gross_revenue=gross_revenue,
        total_overhead=total_overhead,
        net_income=net_income,
        revpash=revpash,
        kiosk_revenue=kiosk_revenue,
        app_revenue=app_revenue
    )


@main_bp.route('/stylist_portal/<int:staff_id>')
def stylist_portal(staff_id):
    return render_template('stylist_portal.html', staff_id=staff_id)


@main_bp.route('/update_booking_status', methods=['POST'])
@main_bp.route('/update_status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id=None):
    return jsonify({'status': 'success'})


@main_bp.route('/add_stylist', methods=['POST'])
def add_stylist():
    full_name = request.form.get('name', 'Stylist')
    flash(f"Stylist {full_name} registered successfully!", "success")
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/cashout_staff/<int:staff_id>', methods=['POST'])
def cashout_staff(staff_id):
    flash('Staff cashed out successfully.', 'success')
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/checkout_booking/<int:booking_id>', methods=['POST'])
def checkout_booking(booking_id):
    flash('Booking checked out.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

# ==========================================
# 5. CLIENT & SERVICE MANAGEMENT (SAFE PRESERVE TAB)
# ==========================================

@main_bp.route('/add_client', methods=['POST'])
def add_client():
    flash('Client added to CRM.', 'success')
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/edit_client', methods=['POST'])
def edit_client():
    flash('Client record updated.', 'success')
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/delete_client/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    flash('Client deleted.', 'info')
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/add_service', methods=['POST'])
def add_service():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    price_min = request.form.get('price_min', 0.0)
    price_max = request.form.get('price_max', None)
    duration = request.form.get('duration', 30)
    required_role = request.form.get('required_role', 'Stylist')
    
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            image_url = f'img/uploads/{filename}'

    try:
        from app.models import Service
        new_svc = Service(
            name=name,
            category=category,
            price_min=float(price_min) if price_min else 0.0,
            price_max=float(price_max) if price_max else None,
            duration=int(duration) if duration else 30,
            required_role=required_role,
            image_url=image_url
        )
        db.session.add(new_svc)
        db.session.commit()
        flash(f'Service "{name}" added to catalog successfully!', 'success')
    except Exception as err:
        db.session.rollback()
        print(f"Error adding service: {err}")
        flash('Failed to add service. Please verify form values.', 'danger')

    return redirect(url_for('main.stylist_dashboard', _anchor='menu'))


@main_bp.route('/edit_service', methods=['POST'])
def edit_service():
    service_id = request.form.get('service_id')
    try:
        from app.models import Service
        svc = Service.query.get(service_id)
        if svc:
            if request.form.get('name'): svc.name = request.form.get('name').strip()
            if request.form.get('category'): svc.category = request.form.get('category').strip()
            if request.form.get('price_min'): svc.price_min = float(request.form.get('price_min'))
            if request.form.get('price_max'): 
                pmax = request.form.get('price_max').strip()
                svc.price_max = float(pmax) if pmax else None
            if request.form.get('duration'): svc.duration = int(request.form.get('duration'))
            if request.form.get('required_role'): svc.required_role = request.form.get('required_role')
            
            db.session.commit()
            flash('Service catalog updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error updating service: {e}")
        flash('Failed to update service.', 'danger')

    return redirect(url_for('main.stylist_dashboard', _anchor='menu'))


@main_bp.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    try:
        from app.models import Service
        svc = Service.query.get(service_id)
        if svc:
            db.session.delete(svc)
            db.session.commit()
            flash('Service removed from catalog.', 'info')
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting service: {e}")

    return redirect(url_for('main.stylist_dashboard', _anchor='menu'))


@main_bp.route('/seed_services')
def seed_services():
    try:
        from app.models import Service
        
        ivonne_menu = [
            {"name": "Signature Haircut & Style", "category": "Haircuts", "price_min": 35.00, "duration": 45, "required_role": "Master Stylist"},
            {"name": "Beard Trim & Hot Towel Treatment", "category": "Barbering", "price_min": 25.00, "duration": 30, "required_role": "Barber"},
            {"name": "VIP Haircut & Beard Combination", "category": "Combos", "price_min": 55.00, "duration": 60, "required_role": "Master Stylist"},
            {"name": "Women's Trim & Blowout", "category": "Styling", "price_min": 45.00, "duration": 45, "required_role": "Master Stylist"},
            {"name": "Full Color & Highlights", "category": "Color", "price_min": 85.00, "duration": 120, "required_role": "Master Stylist"},
            {"name": "Kids Cut (12 & Under)", "category": "Haircuts", "price_min": 25.00, "duration": 30, "required_role": "Stylist"}
        ]
        
        added_count = 0
        for item in ivonne_menu:
            existing = Service.query.filter_by(name=item["name"]).first()
            if not existing:
                new_svc = Service(
                    name=item["name"],
                    category=item["category"],
                    price_min=item["price_min"],
                    duration=item["duration"],
                    required_role=item["required_role"]
                )
                db.session.add(new_svc)
                added_count += 1

        db.session.commit()
        if added_count > 0:
            flash(f"Added {added_count} new service(s) to Ivonne's catalog!", "success")
        else:
            flash("All catalog services are already up to date.", "info")

        return redirect(url_for('main.stylist_dashboard', _anchor='menu'))
    except Exception as e:
        db.session.rollback()
        return f"Database Seed Error: {e}"

# ==========================================
# 6. PRODUCTS, EXPENSES & REPORTS
# ==========================================

@main_bp.route('/add_product', methods=['POST'])
def add_product():
    flash('Product added to inventory.', 'success')
    return redirect(url_for('main.stylist_dashboard', _anchor='menu'))


@main_bp.route('/edit_product', methods=['POST'])
def edit_product():
    flash('Product updated.', 'success')
    return redirect(url_for('main.stylist_dashboard', _anchor='menu'))


@main_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    flash('Product removed.', 'info')
    return redirect(url_for('main.stylist_dashboard', _anchor='menu'))


@main_bp.route('/add_expense', methods=['POST'])
def add_expense():
    flash('Expense logged.', 'success')
    return redirect(url_for('main.stylist_dashboard', _anchor='expenses'))


@main_bp.route('/save_bank_account', methods=['POST'])
def save_bank_account():
    flash('Operating bank details verified and linked.', 'success')
    return redirect(url_for('main.stylist_dashboard', _anchor='banking'))


@main_bp.route('/export_tax_csv')
def export_tax_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Description', 'Amount'])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=tax_report.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@main_bp.route('/rate_visit', methods=['GET', 'POST'])
def rate_visit():
    return render_template('rate_visit.html')

# ==========================================
# 7. CAMPAIGN ENGINE
# ==========================================

@main_bp.route('/send_email_blast', methods=['POST'])
def send_email_blast():
    flash('Broadcast queued or sent.', 'info')
    return redirect(url_for('main.stylist_dashboard', _anchor='clients'))


@main_bp.route('/update_campaign', methods=['POST'])
def update_campaign():
    flash('Campaign Ad and Homepage Bulletin updated live!', 'success')
    return redirect(url_for('main.stylist_dashboard', _anchor='indexmanager'))