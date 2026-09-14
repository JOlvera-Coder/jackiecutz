import csv
import random
from io import StringIO
from collections import Counter
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from app.models import db, User, Booking, ServiceCatalog

main_bp = Blueprint('main', __name__)

# --- LOGIN & AUTH ROUTES ---
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        flash('Login successful!', 'success')
        return redirect(url_for('main.stylist_dashboard'))
    endpoints = ['forgot_password', 'register', 'terms', 'privacy']
    return render_template('login.html', endpoints=endpoints)

@main_bp.route('/logout')
def logout():
    return redirect(url_for('main.login'))

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        zip_code = request.form.get('zip', '').strip()
        gender = request.form.get('gender')
        birthday = request.form.get('birthday')

        full_name = f"{first_name} {last_name}".strip() if last_name else first_name

        existing = User.query.filter((User.email == email) | (User.phone == phone)).first() if (email or phone) else None
        if existing:
            flash("An account with this email or phone number already exists.", "danger")
            return redirect(url_for('main.login'))

        new_client = User(
            name=full_name,
            phone=phone,
            email=email,
            source_channel='Registration'
        )

        if hasattr(new_client, 'zip_code'): setattr(new_client, 'zip_code', zip_code)
        if hasattr(new_client, 'gender'): setattr(new_client, 'gender', gender)
        if hasattr(new_client, 'birthday'): setattr(new_client, 'birthday', birthday)
        if hasattr(new_client, 'set_password'): new_client.set_password(password)

        db.session.add(new_client)
        db.session.commit()
        flash("Registration successful!", "success")
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

# --- CUSTOMER PORTAL & BOOKING ROUTES ---
@main_bp.route('/customer_portal')
@main_bp.route('/client_dashboard')
def customer_portal():
    services = ServiceCatalog.query.all()
    for s in services:
        if not hasattr(s, 'price') or s.price is None:
            s.price = getattr(s, 'price_min', 35.0)
    return render_template('booking.html', services=services)

@main_bp.route('/book_service', methods=['POST'])
def book_service():
    service_id = request.form.get('service_id')
    client_name = request.form.get('client_name', 'Client')
    client_phone = request.form.get('client_phone', '')
    
    svc = ServiceCatalog.query.get(service_id) if service_id else None
    svc_name = svc.name if svc else "Haircut Service"
    svc_price = getattr(svc, 'price_min', 35.0) if svc else 35.0
    
    user = User.query.filter_by(phone=client_phone).first() if client_phone else None
    if not user:
        user = User(name=client_name, phone=client_phone, email=f"client_{random.randint(1000,9999)}@jackiecutz.com", source_channel='Mobile App')
        db.session.add(user)
        db.session.commit()
        
    new_b = Booking(
        user_id=user.id,
        service_name=svc_name,
        price=svc_price,
        status='in-queue',
        source_channel='Mobile App'
    )
    db.session.add(new_b)
    db.session.commit()
    flash(f"Appointment booked for {client_name}!", "success")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/api/available-slots')
@main_bp.route('/api/get_slots')
def available_slots():
    slots = ["10:00 AM", "10:45 AM", "11:30 AM", "12:15 PM", "01:00 PM", "01:45 PM", "02:30 PM", "03:15 PM", "04:00 PM", "04:45 PM", "05:30 PM"]
    return jsonify({'slots': slots, 'status': 'open'})

# --- STYLIST DASHBOARD & COMMAND CENTER ---
@main_bp.route('/dashboard')
@main_bp.route('/stylist_dashboard')
def stylist_dashboard():
    bookings = Booking.query.order_by(Booking.id.desc()).all()
    users = User.query.all()
    services = ServiceCatalog.query.all()
    
    user_zips = [u.zip_code for u in users if getattr(u, 'zip_code', None)]
    zip_counts = dict(Counter(user_zips)) if user_zips else {'77073': len(users)}

    staff = Staff.query.all() if 'Staff' in globals() else []
    products = Product.query.all() if 'Product' in globals() else []
    expenses = Expense.query.order_by(Expense.id.desc()).all() if 'Expense' in globals() else []
    
    bank_record = BankAccount.query.first() if 'BankAccount' in globals() else None
    bank = {
        'status': getattr(bank_record, 'status', 'Active'),
        'account': getattr(bank_record, 'account_number', 'N/A'),
        'bank_name': getattr(bank_record, 'bank_name', 'N/A')
    } if bank_record else {'status': 'Active', 'account': 'Primary Account', 'bank_name': 'Business Deposit'}

    return render_template(
        'dashboard.html', 
        bookings=bookings, 
        users=users, 
        services=services, 
        zip_counts=zip_counts,
        bank=bank, 
        staff=staff, 
        products=products, 
        expenses=expenses
    )

@main_bp.route('/update_booking_status', methods=['POST'])
@main_bp.route('/update_status/<int:booking_id>', methods=['POST'])
def update_booking_status(booking_id=None):
    b_id = booking_id or request.form.get('booking_id')
    new_status = request.form.get('status', 'completed')
    if b_id:
        b = Booking.query.get(b_id)
        if b:
            b.status = new_status
            db.session.commit()
            flash(f"Booking #{b_id} status updated to {new_status}.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_stylist', methods=['POST'])
def add_stylist():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    flash(f"Stylist {full_name} registered successfully!", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/cashout_staff/<int:staff_id>', methods=['POST'])
def cashout_staff(staff_id):
    flash(f"Cashout processed for staff #{staff_id}.", "success")
    return redirect(url_for('main.stylist_dashboard'))

from datetime import datetime

@main_bp.route('/stylist_portal/<int:staff_id>')
def stylist_portal(staff_id):
    # Fetch live active queue items and today's completed haircuts
    active_bookings = Booking.query.filter(Booking.status.in_(['in-queue', 'servicing'])).order_by(Booking.id.asc()).all()
    completed_today = Booking.query.filter_by(status='completed').order_by(Booking.id.desc()).all()
    
    return render_template(
        'stylist_portal.html', 
        staff_id=staff_id, 
        bookings=active_bookings, 
        completed=completed_today
    )

@main_bp.route('/checkout_booking/<int:booking_id>', methods=['POST'])
def checkout_booking(booking_id):
    payment_method = request.form.get('payment_method', 'Card Terminal')
    tip_amount = float(request.form.get('tip', 0.0) or 0.0)
    staff_id = request.form.get('staff_id', 1)

    booking = Booking.query.get(booking_id)
    if booking:
        # Write live checkout transaction directly to SQLAlchemy DB
        booking.status = 'completed'
        booking.payment_method = payment_method
        booking.tip = tip_amount
        booking.completed_at = datetime.utcnow()
        
        db.session.commit()
        flash(f"Booking #{booking_id} closed out successfully! Payment: {payment_method} | Tip: ${tip_amount:.2f}", "success")
    else:
        flash("Booking record not found.", "danger")

    return redirect(url_for('main.stylist_portal', staff_id=staff_id))

@main_bp.route('/add_client', methods=['POST'])
def add_client():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    zip_code = request.form.get('zip', '').strip()
    
    new_user = User(
        name=full_name, 
        phone=phone, 
        email=email, 
        source_channel='Command Center'
    )
    if hasattr(new_user, 'zip_code'): 
        setattr(new_user, 'zip_code', zip_code)
        
    db.session.add(new_user)
    db.session.commit()
    flash(f"Client {full_name} added to CRM!", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_client', methods=['POST'])
def edit_client():
    flash("Client details updated.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_client/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    u = User.query.get(client_id)
    if u:
        db.session.delete(u)
        db.session.commit()
        flash(f"Client #{client_id} removed.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_service', methods=['POST'])
def add_service():
    name = request.form.get('name', 'New Service')
    price = request.form.get('price', 35.0)
    new_svc = ServiceCatalog(name=name, price_min=price)
    db.session.add(new_svc)
    db.session.commit()
    flash(f"Service {name} added!", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_service', methods=['POST'])
def edit_service():
    flash("Service updated.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    svc = ServiceCatalog.query.get(service_id)
    if svc:
        db.session.delete(svc)
        db.session.commit()
        flash(f"Service #{service_id} deleted.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_product', methods=['POST'])
def add_product():
    flash("Product added to inventory.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_product', methods=['POST'])
def edit_product():
    flash("Product updated.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    flash(f"Product #{product_id} deleted.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_expense', methods=['POST'])
def add_expense():
    flash("Expense recorded.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/save_bank_account', methods=['POST'])
def save_bank_account():
    flash("Bank details updated.", "success")
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/walkin_kiosk')
def walkin_kiosk():
    return render_template('kiosk.html')

@main_bp.route('/queue_display')
def queue_display():
    bookings = Booking.query.filter_by(status='in-queue').all()
    clients = User.query.all()
    return render_template('queue_display.html', bookings=bookings, clients=clients)

@main_bp.route('/export_tax_csv')
def export_tax_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Booking ID', 'Client Name', 'Service', 'Price', 'Status', 'Channel'])
    bookings = Booking.query.all()
    for b in bookings:
        cw.writerow([b.id, getattr(b, 'user_name', 'Client'), b.service_name, b.price, b.status, b.source_channel])
    output = si.getvalue()
    return Response(output, mimetype="text/csv", headers={"Content-Disposition": "attachment;filename=tax_report.csv"})

@main_bp.route('/rate_visit', methods=['GET', 'POST'])
def rate_visit():
    if request.method == 'POST':
        rating = int(request.form.get('rating', 5))
        if rating >= 4:
            return redirect("https://g.page/r/CafPhbBwHLHwEAI/review")
        flash("Thank you for your feedback!", "success")
        return redirect(url_for('main.customer_portal'))
    return render_template('rate_visit.html')