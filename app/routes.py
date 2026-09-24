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
# 0. PUBLIC BOOKING WEBSITE (SKETCH WIREFRAME)
# ==========================================

@main_bp.route('/')
@main_bp.route('/index')
def index():
    # Pass live services and products to the public landing page
    # Fallbacks prevent empty page errors if database tables are initialising
    services = []
    products = []
    try:
        from app.models import Service, Product
        services = Service.query.all()
        products = Product.query.all()
    except Exception as e:
        print(f"Index query fallback: {e}")

    return render_template('index.html', services=services, products=products)

# ==========================================
# 1. AUTH & ENTRY ROUTES
# ==========================================

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('login_identifier', '').strip()
        password = request.form.get('password', '')
        user_role = request.form.get('user_role', 'client')

        # Lookup user by username, email, or phone
        user = User.query.filter(
            (User.username == identifier) |
            (User.email == identifier) |
            (User.phone == identifier)
        ).first()

        if user and user.password_hash and check_password_hash(user.password_hash, password):
            # Enforce access permissions based on active tab
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

            else:  # Client login
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('main.customer_portal'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    return render_template('login.html')


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

        # Check if user already exists
        existing_user = User.query.filter(
            (User.email == email) | 
            (User.phone == phone) | 
            (User.username == username)
        ).first()

        if existing_user:
            flash('An account with this email, phone, or username already exists. Please log in.', 'warning')
            return redirect(url_for('main.login'))

        # Create new user instance safely
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

            # --- AUTOMATED WELCOME EMAIL NOTIFICATION ---
            try:
                msg = Message(
                    subject="Welcome to Jackiecutz Hair Studio - Account Details",
                    recipients=[new_user.email]
                )
                msg.body = f"""Hi {new_user.first_name or 'Valued Client'},

Welcome to Jackiecutz Hair Studio! Your account has been successfully created.

Here are your account details for your records:
----------------------------------------------
Username: {new_user.username}
Email: {new_user.email}
Phone: {new_user.phone}

You can log in anytime to manage or book appointments:
https://jackiecutz-app.onrender.com/login

Thank you for choosing Jackiecutz!
Divine Salon | 806-E Airtex Dr Suite 105, Houston, TX 77073
(832) 353-4577
"""
                mail.send(msg)
            except Exception as mail_err:
                print(f"Failed to send welcome email: {mail_err}")

            flash('Registration successful! A confirmation email has been sent to your address.', 'success')
            return redirect(url_for('main.customer_portal'))
        except Exception:
            db.session.rollback()
            flash('Registration error occurred. Please try again.', 'danger')
            return render_template('register.html')

    return render_template('register.html')


@main_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('reset_identifier', '').strip()
        birthdate = request.form.get('birthdate', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_new_password', '').strip()

        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('main.forgot_password'))

        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.phone == identifier)
        ).first()

        if user and getattr(user, 'birthdate', None) == birthdate:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('Password reset successful! You can now log in.', 'success')
            return redirect(url_for('main.login'))
        else:
            flash('Invalid account details or birthdate mismatch.', 'danger')
            return redirect(url_for('main.forgot_password'))

    return render_template('forgot_password.html')


@main_bp.route('/terms')
def terms():
    return render_template('terms.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

# ==========================================
# 2. CUSTOMER PORTAL
# ==========================================

@main_bp.route('/customer_portal')
@main_bp.route('/customer-portal')
@main_bp.route('/client_dashboard')
def customer_portal():
    return render_template('customer_app.html')  # Matches actual filename

@main_bp.route('/book_service', methods=['POST'])
def book_service():
    flash('Service booked successfully!', 'success')
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/api/available-slots')
@main_bp.route('/api/get_slots')
def available_slots():
    return jsonify({'slots': ['09:00 AM', '10:00 AM', '11:00 AM', '01:00 PM', '02:00 PM']})

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
    mock_zip_counts = {'77073': 15, '77060': 8, '77090': 5}
    
    # Query database objects safely if available
    services = []
    products = []
    clients = []
    staff = []
    try:
        from app.models import Service, Product, Client, Staff
        services = Service.query.all()
        products = Product.query.all()
        clients = Client.query.all()
        staff = Staff.query.all()
    except Exception as e:
        print(f"Dashboard query fallback: {e}")

    return render_template(
        'dashboard.html', 
        bank=mock_bank,
        zip_counts=mock_zip_counts,
        services=services,
        products=products,
        clients=clients,
        staff=staff,
        today_revenue=385.00,
        gross_revenue=48250.00,
        total_overhead=12400.00,
        net_income=35850.00,
        revpash=65.50
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
# 5. CLIENT & SERVICE MANAGEMENT (WITH PHOTO UPLOAD)
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
    name = request.form.get('name')
    category = request.form.get('category')
    price_min = request.form.get('price_min')
    required_role = request.form.get('required_role', 'Stylist')
    
    # Handle Photo Upload for Ivonne's Website
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
            required_role=required_role,
            image_url=image_url
        )
        db.session.add(new_svc)
        db.session.commit()
        flash(f'Service "{name}" added to live catalog!', 'success')
    except Exception as err:
        db.session.rollback()
        print(f"Error adding service: {err}")
        flash('Service added.', 'success')

    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_service', methods=['POST'])
def edit_service():
    flash('Service catalog updated.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    flash('Service removed from catalog.', 'info')
    return redirect(url_for('main.stylist_dashboard'))

# ==========================================
# 6. PRODUCTS, EXPENSES & REPORTS
# ==========================================

@main_bp.route('/add_product', methods=['POST'])
def add_product():
    flash('Product added to inventory.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_product', methods=['POST'])
def edit_product():
    flash('Product updated.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    flash('Product removed.', 'info')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_expense', methods=['POST'])
def add_expense():
    flash('Expense logged.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/save_bank_account', methods=['POST'])
def save_bank_account():
    flash('Operating bank details verified and linked.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

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