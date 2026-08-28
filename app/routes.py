from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, jsonify, Response
from app import db
from app.models import User, Customer, FamilyMember, BarberBooking, BarberService, Product, StudioExpense, ExpenseCategory
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date, timedelta
import csv
import io
import re

main_bp = Blueprint('main', __name__)

def clean_phone(phone_str):
    if not phone_str:
        return ""
    return re.sub(r'\D', '', str(phone_str))

DEFAULT_TIME_SLOTS = [
    "09:00 AM", "09:30 AM", "10:00 AM", "10:30 AM",
    "11:00 AM", "11:30 AM", "12:00 PM", "12:30 PM",
    "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM",
    "03:00 PM", "03:30 PM", "04:00 PM", "04:30 PM",
    "05:00 PM", "05:30 PM", "06:00 PM"
]

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

        # 1. Stylist / Admin Check (Ivonne)
        user = User.query.filter(
            (User.username.ilike(identifier)) | 
            (User.email.ilike(identifier))
        ).first()

        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session['user_id'] = user.id
            session['is_admin'] = getattr(user, 'is_admin', True)
            session.permanent = remember
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('main.stylist_dashboard'))

        # 2. Universal Customer Lookup (Username, Phone, Name, or Email)
        customer = None
        if digits and len(digits) >= 7:
            customer = Customer.query.filter(Customer.phone == digits).first()

        if not customer and hasattr(Customer, 'username') and identifier:
            customer = Customer.query.filter(Customer.username.ilike(identifier)).first()

        if not customer and identifier:
            customer = Customer.query.filter(
                (Customer.name.ilike(identifier)) |
                (Customer.name.ilike(f"%{identifier}%")) |
                (Customer.email.ilike(identifier))
            ).first()

        if customer:
            session.clear()
            session['customer_id'] = customer.id
            session.permanent = remember
            return redirect(url_for('main.customer_portal'))

        flash("Username, phone, or credentials not recognized. Please try again or register.", "danger")
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

        if not first_name and not username:
            flash("Please enter a name or username.", "danger")
            return render_template('register.html', form_data=form_data)
        if not phone or len(phone) < 10:
            flash("Please enter a valid 10-digit phone number.", "danger")
            return render_template('register.html', form_data=form_data)
        if not zip_code:
            flash("Please enter a zip code.", "danger")
            return render_template('register.html', form_data=form_data)

        existing_phone = Customer.query.filter(Customer.phone == phone).first()
        if existing_phone:
            session.clear()
            session['customer_id'] = existing_phone.id
            return redirect(url_for('main.customer_portal'))

        new_customer = Customer(
            username=username if username else None,
            name=full_name,
            phone=phone,
            email=email if email else None,
            gender=gender if gender else None,
            birthday=birthday if birthday else None,
            zip_code=zip_code if zip_code else None
        )
        db.session.add(new_customer)
        db.session.commit()

        session.clear()
        session['customer_id'] = new_customer.id
        return redirect(url_for('main.customer_portal'))

    return render_template('register.html', form_data=form_data)

@main_bp.route('/booking')
@main_bp.route('/customer/portal')
def customer_portal():
    if 'customer_id' not in session:
        return redirect(url_for('main.login'))
    customer = Customer.query.get(session['customer_id'])
    services = BarberService.query.all()
    user_bookings = BarberBooking.query.filter_by(customer_id=customer.id).order_by(BarberBooking.appointment_time.desc()).all() if customer else []
    family_members = FamilyMember.query.filter_by(customer_id=customer.id).all() if customer else []
    return render_template('booking.html', customer=customer, services=services, time_slots=DEFAULT_TIME_SLOTS, bookings=user_bookings, family_members=family_members)

@main_bp.route('/update-profile', methods=['POST'])
def update_profile():
    if 'customer_id' not in session:
        return redirect(url_for('main.login'))
    customer = Customer.query.get(session['customer_id'])
    if customer:
        customer.name = request.form.get('name', customer.name).strip()
        customer.email = request.form.get('email', customer.email).strip()
        customer.zip_code = request.form.get('zip_code', customer.zip_code).strip()
        db.session.commit()
        flash("Profile updated successfully!", "success")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/add-family-member', methods=['POST'])
def add_family_member():
    if 'customer_id' not in session:
        return redirect(url_for('main.login'))
    name = request.form.get('name', '').strip()
    relationship = request.form.get('relationship', 'Child').strip()
    notes = request.form.get('notes', '').strip()
    
    if name:
        member = FamilyMember(
            customer_id=session['customer_id'],
            name=name,
            relationship=relationship,
            notes=notes
        )
        db.session.add(member)
        db.session.commit()
        flash(f"Added {name} to your family profile!", "success")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/delete-family-member/<int:member_id>', methods=['POST'])
def delete_family_member(member_id):
    if 'customer_id' not in session:
        return redirect(url_for('main.login'))
    member = FamilyMember.query.get_or_404(member_id)
    if member.customer_id == session['customer_id']:
        db.session.delete(member)
        db.session.commit()
        flash("Family member removed.", "info")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/book-service', methods=['POST'])
def book_service():
    if 'customer_id' not in session:
        return redirect(url_for('main.login'))
    customer = Customer.query.get(session['customer_id'])
    
    service_id = request.form.get('service_id')
    service = BarberService.query.get(service_id) if service_id else None
    service_name = service.name if service else request.form.get('service_name', 'Signature Haircut')
    price = service.price if service else 35.0

    booking = BarberBooking(
        customer_id=customer.id if customer else None,
        service_name=service_name,
        price=price,
        status="Confirmed",
        appointment_time=datetime.utcnow()
    )
    db.session.add(booking)
    db.session.commit()

    flash(f"Appointment booked successfully for {service_name}!", "success")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'customer_id' not in session:
        return redirect(url_for('main.login'))
    booking = BarberBooking.query.get_or_404(booking_id)
    if booking.customer_id == session['customer_id']:
        booking.status = "Cancelled"
        db.session.commit()
        flash("Booking cancelled successfully.", "info")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/reschedule-booking/<int:booking_id>', methods=['POST'])
def reschedule_booking(booking_id):
    if 'customer_id' not in session:
        return redirect(url_for('main.login'))
    booking = BarberBooking.query.get_or_404(booking_id)
    if booking.customer_id == session['customer_id']:
        booking.status = "Rescheduled"
        db.session.commit()
        flash("Appointment rescheduled.", "info")
    return redirect(url_for('main.customer_portal'))

@main_bp.route('/walkin-kiosk', methods=['GET', 'POST'])
def walkin_kiosk():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        phone = clean_phone(request.form.get('phone', ''))
        email = request.form.get('email', '').strip()
        zip_code = request.form.get('zip_code', '77073').strip()
        service_name = request.form.get('service', 'Signature Haircut')

        if not phone or len(phone) < 10:
            flash("Please provide a valid 10-digit phone number.", "danger")
            return redirect(url_for('main.walkin_kiosk'))

        customer = Customer.query.filter(Customer.phone == phone).first()
        if not customer:
            customer = Customer(
                name=full_name if full_name else "Walk-In Client",
                phone=phone,
                email=email if email else None,
                zip_code=zip_code
            )
            db.session.add(customer)
            db.session.commit()

        booking = BarberBooking(
            customer_id=customer.id,
            service_name=service_name,
            status="In Queue",
            price=35.0,
            appointment_time=datetime.utcnow()
        )
        db.session.add(booking)
        db.session.commit()

        flash(f"Thank you, {customer.name}! You are on today's active chair waitlist for {service_name}.", "success")
        return redirect(url_for('main.walkin_kiosk'))

    services = BarberService.query.all()
    return render_template('kiosk.html', services=services)

@main_bp.route('/admin')
@main_bp.route('/stylist/dashboard')
def stylist_dashboard():
    if 'user_id' not in session:
        flash("Please log in as a stylist to access the command center.", "warning")
        return redirect(url_for('main.login'))

    total_revenue = sum([b.price for b in BarberBooking.query.filter(BarberBooking.status == 'Completed').all()]) or 0.0
    total_clients = Customer.query.count()
    active_bookings = BarberBooking.query.order_by(BarberBooking.appointment_time.desc()).limit(15).all()

    chart_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    chart_data = [120, 180, 240, 210, 320, 450, 380]
    chart_channel_labels = ["Walk-in Kiosk", "Online Booking", "Phone / Direct"]
    chart_channel_data = [45, 35, 20]
    recent_activity = active_bookings

    return render_template(
        'dashboard.html',
        total_revenue=total_revenue,
        total_clients=total_clients,
        active_bookings=active_bookings,
        chart_labels=chart_labels,
        chart_data=chart_data,
        chart_channel_labels=chart_channel_labels,
        chart_channel_data=chart_channel_data,
        recent_activity=recent_activity
    )

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been securely signed out.", "info")
    return redirect(url_for('main.login'))

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        digits = clean_phone(identifier)
        customer = Customer.query.filter(
            (Customer.phone == digits) | (Customer.email.ilike(identifier))
        ).first() if (digits or identifier) else None

        if customer:
            flash(f"Account match confirmed for {customer.name}. Sign in directly with your phone ({customer.phone}).", "success")
            return redirect(url_for('main.login'))
        flash("No matching record found. Please check your phone number or register.", "danger")
    return render_template('forgot_password.html')