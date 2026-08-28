import os
import math
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Appointment, Service

main_bp = Blueprint('main', __name__)

# Jackie Cutz Salon Coordinates & 10ft Geofence
SALON_LAT = 29.7604
SALON_LNG = -95.3698
GEOFENCE_RADIUS_METERS = 3.05  # Exactly 10 feet (3.05 meters)


def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) *
         math.sin(delta_lambda / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# -------------------------------------------------------------
# AUTHENTICATION ROUTES
# -------------------------------------------------------------
@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'stylist':
            return redirect(url_for('main.stylist_dashboard'))
        return redirect(url_for('main.client_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'stylist':
                return redirect(url_for('main.stylist_dashboard'))
            return redirect(url_for('main.client_dashboard'))
        flash('Invalid email or password.', 'error')

    return render_template('login.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('main.register'))

        new_user = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role='client'
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main.client_dashboard'))

    return render_template('register.html')


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


# -------------------------------------------------------------
# CLIENT DASHBOARD & BOOKING
# -------------------------------------------------------------
@main_bp.route('/dashboard')
@login_required
def client_dashboard():
    services = Service.query.all()
    user_appts = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.id.desc()).all()
    return render_template('booking.html', services=services, appointments=user_appts)


# -------------------------------------------------------------
# WALK-IN KIOSK TERMINAL (With 6-Sec Confirmation & Cash/App Tag)
# -------------------------------------------------------------
@main_bp.route('/kiosk', methods=['GET', 'POST'])
def walkin_kiosk():
    success_client = None
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        service_id = request.form.get('service_id')
        payment_method = request.form.get('payment_method', 'in_app')

        client_name = f"{first_name} {last_name}".strip()

        queue_count = Appointment.query.filter(
            Appointment.status.in_(['waiting', 'checked_in', 'in_chair'])
        ).count()

        new_walkin = Appointment(
            client_name=client_name,
            phone=phone,
            email=email,
            service_id=int(service_id) if service_id and service_id.isdigit() else None,
            status='waiting',
            date=datetime.utcnow().date(),
            time=datetime.utcnow().strftime("%I:%M %p")
        )
        if hasattr(Appointment, 'payment_status'):
            new_walkin.payment_status = payment_method

        db.session.add(new_walkin)
        db.session.commit()

        success_client = {
            'name': client_name,
            'position': queue_count + 1
        }

    services = Service.query.all()
    return render_template('kiosk.html', services=services, success_client=success_client)


# -------------------------------------------------------------
# LIVE PUBLIC TV QUEUE DISPLAY (/queue and /tv)
# -------------------------------------------------------------
@main_bp.route('/queue')
@main_bp.route('/tv')
def live_queue_display():
    in_chair = Appointment.query.filter_by(status='in_chair').first()
    waiting_list = Appointment.query.filter(
        Appointment.status.in_(['waiting', 'checked_in'])
    ).order_by(Appointment.id.asc()).all()

    return render_template(
        'queue_display.html',
        in_chair=in_chair,
        waiting_list=waiting_list,
        total_waiting=len(waiting_list)
    )


# -------------------------------------------------------------
# STYLIST COMMAND CENTER & CHECKOUT ACTIONS
# -------------------------------------------------------------
@main_bp.route('/stylist/dashboard')
@login_required
def stylist_dashboard():
    in_chair = Appointment.query.filter_by(status='in_chair').first()
    waiting_list = Appointment.query.filter(
        Appointment.status.in_(['waiting', 'checked_in'])
    ).order_by(Appointment.id.asc()).all()
    completed_today = Appointment.query.filter_by(status='completed').all()

    return render_template(
        'dashboard.html',
        in_chair=in_chair,
        waiting_list=waiting_list,
        completed_today=completed_today
    )


@main_bp.route('/stylist/call-chair/<int:appt_id>', methods=['POST'])
@login_required
def call_chair(appt_id):
    current_chair = Appointment.query.filter_by(status='in_chair').first()
    if current_chair:
        current_chair.status = 'completed'

    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'in_chair'
    db.session.commit()
    flash(f"{appt.client_name} called to chair!", "success")
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/stylist/complete-checkout/<int:appt_id>', methods=['POST'])
@login_required
def complete_checkout(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'completed'
    db.session.commit()
    flash(f"Service completed and closed for {appt.client_name}!", "success")
    return redirect(url_for('main.stylist_dashboard'))


# -------------------------------------------------------------
# 10-FOOT GEOFENCE AUTO CHECK-IN API
# -------------------------------------------------------------
@main_bp.route('/api/geofence-checkin', methods=['POST'])
@login_required
def geofence_checkin():
    data = request.get_json() or {}
    user_lat = data.get('lat')
    user_lng = data.get('lng')

    if user_lat is None or user_lng is None:
        return jsonify({'status': 'error', 'message': 'Missing coordinates'}), 400

    distance = calculate_haversine_distance(float(user_lat), float(user_lng), SALON_LAT, SALON_LNG)

    if distance <= GEOFENCE_RADIUS_METERS:
        appt = Appointment.query.filter_by(
            user_id=current_user.id,
            status='booked'
        ).first()

        if appt:
            appt.status = 'checked_in'
            db.session.commit()
            return jsonify({
                'status': 'checked_in',
                'message': 'Auto-detected within 10 feet! You are checked in.',
                'distance_feet': round(distance * 3.28084, 1)
            }), 200

        return jsonify({
            'status': 'already_checked_in_or_no_appt',
            'distance_feet': round(distance * 3.28084, 1)
        }), 200

    return jsonify({
        'status': 'outside_geofence',
        'distance_feet': round(distance * 3.28084, 1)
    }), 200