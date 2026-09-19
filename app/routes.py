import csv
import io
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, jsonify, make_response
)
from app.models import User
from app import db
# Import your models below as needed (e.g., User, Booking, Stylist, Service, etc.)

main_bp = Blueprint('main', __name__)

# ==========================================
# 1. AUTH & ENTRY ROUTES
# ==========================================

@main_bp.route('/')
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('login_identifier', '').strip()
        password = request.form.get('password', '')

        # Lookup user by username, email, or phone
        user = User.query.filter(
            (User.username == identifier) | 
            (User.email == identifier) | 
            (User.phone == identifier)
        ).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful!', 'success')

            # Route conditionally based on user role
            if getattr(user, 'is_stylist', False):
                return redirect(url_for('main.stylist_dashboard'))
            return redirect(url_for('main.customer_portal'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')

    endpoints = ['forgot_password', 'register', 'terms', 'privacy']
    return render_template('login.html', endpoints=endpoints)


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

        # Create new user instance
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
            is_stylist=False  # New self-registrations default to client
        )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)

        flash('Registration successful!', 'success')

        if new_user.is_stylist:
            return redirect(url_for('main.stylist_dashboard'))
        return redirect(url_for('main.customer_portal'))

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
# --- CUSTOMER PORTAL FIX ---
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
# --- DASHBOARD FIX ---
@main_bp.route('/dashboard')
@main_bp.route('/stylist_dashboard')
@main_bp.route('/stylist-dashboard')
def stylist_dashboard():
    mock_bank = {'status': 'Connected', 'account_number': '•••• 1234'}
    mock_zip_counts = {'77073': 15, '77060': 8, '77090': 5}
    mock_stylists = []
    mock_bookings = []
    mock_expenses = []
    
    return render_template(
        'dashboard.html', 
        bank=mock_bank,
        zip_counts=mock_zip_counts,
        stylists=mock_stylists,
        bookings=mock_bookings,
        expenses=mock_expenses
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
    full_name = request.form.get('full_name', 'Stylist')
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
# 5. CLIENT & SERVICE MANAGEMENT
# ==========================================

@main_bp.route('/add_client', methods=['POST'])
def add_client():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_client', methods=['POST'])
def edit_client():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_client/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_service', methods=['POST'])
def add_service():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_service', methods=['POST'])
def edit_service():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    return redirect(url_for('main.stylist_dashboard'))

# ==========================================
# 6. PRODUCTS, EXPENSES & REPORTS
# ==========================================

@main_bp.route('/add_product', methods=['POST'])
def add_product():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_product', methods=['POST'])
def edit_product():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_expense', methods=['POST'])
def add_expense():
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/save_bank_account', methods=['POST'])
def save_bank_account():
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