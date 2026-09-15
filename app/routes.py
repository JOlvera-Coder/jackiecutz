import csv
import io
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, jsonify, make_response
)
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
        flash('Login successful!', 'success')
        return redirect(url_for('main.stylist_dashboard'))
    endpoints = ['forgot_password', 'register', 'terms', 'privacy']
    return render_template('login.html', endpoints=endpoints)

@main_bp.route('/logout')
def logout():
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/register', methods=['GET', 'POST'])
@main_bp.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        zip_code = request.form.get('zip_code', '').strip()
        gender = request.form.get('gender')
        birthday = request.form.get('birthday')

        # Add your database user creation logic here
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')

@main_bp.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

# ==========================================
# 2. CUSTOMER & BOOKING ROUTES
# ==========================================

@main_bp.route('/customer_portal')
@main_bp.route('/customer-portal')
@main_bp.route('/client_dashboard')
def customer_portal():
    return render_template('customer_portal.html')

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
    return render_template('dashboard.html')

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