import io
import csv
from datetime import datetime, date
import math
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, func

from app import db
from app.models import User, Service, Appointment

main_bp = Blueprint('main', __name__)

# Divine Salon Coordinates
SALON_LATITUDE = 29.9880
SALON_LONGITUDE = -95.4290
GEOFENCE_RADIUS_MILES = 2.0


def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in miles between two GPS coordinates."""
    r = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


# -------------------------------------------------------------
# STATIC & INFORMATIONAL PAGES
# -------------------------------------------------------------
@main_bp.route('/')
def index():
    return redirect(url_for('main.login'))


@main_bp.route('/terms')
def terms():
    return render_template('terms.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


# -------------------------------------------------------------
# AUTHENTICATION & UNIVERSAL LOGIN
# -------------------------------------------------------------
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'stylist':
            return redirect(url_for('main.stylist_dashboard'))
        return redirect(url_for('main.client_dashboard'))

    if request.method == 'POST':
        identifier = (
            request.form.get('username') or 
            request.form.get('identifier') or 
            request.form.get('email', '')
        ).strip()
        password = request.form.get('password', '')

        clean_phone = ''.join(c for c in identifier if c.isdigit())

        user = User.query.filter(
            or_(
                func.lower(User.email) == identifier.lower(),
                func.lower(User.name) == identifier.lower(),
                func.lower(User.name).like(f"{identifier.lower()}%"),
                (User.phone == clean_phone) if clean_phone else False,
                (User.phone == identifier) if identifier else False
            )
        ).first()

        if user and check_password_hash(user.password_hash, password):
            remember = True if request.form.get('remember') else False
            login_user(user, remember=remember)
            if user.role == 'stylist':
                return redirect(url_for('main.stylist_dashboard'))
            return redirect(url_for('main.client_dashboard'))

        flash('Invalid username, name, phone, or password.', 'error')

    return render_template('login.html')


@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Accept first_name/last_name or full name field
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        name = f"{first_name} {last_name}".strip() or request.form.get('name', '').strip()

        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', 'client123')

        # Fallback generated email if optional in registration UI
        if not email:
            safe_handle = username or first_name.lower() or 'client'
            clean_digits = ''.join(c for c in phone if c.isdigit())[-4:]
            email = f"{safe_handle}_{clean_digits}@jackiecutz.com"

        existing_user = User.query.filter(
            or_(
                User.email == email,
                (User.phone == phone) if phone else False
            )
        ).first()

        if existing_user:
            login_user(existing_user)
            return redirect(url_for('main.client_dashboard'))

        new_user = User(
            name=name or username or "Valued Client",
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


@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        flash('Password reset instructions have been sent if the account exists.', 'info')
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')


@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


# -------------------------------------------------------------
# CLIENT DASHBOARD, BOOKING & CONFIRMATION
# -------------------------------------------------------------
@main_bp.route('/dashboard')
@login_required
def client_dashboard():
    services = Service.query.all()
    user_appts = Appointment.query.filter_by(user_id=current_user.id).order_by(Appointment.id.desc()).all()
    return render_template('booking.html', services=services, appointments=user_appts)


@main_bp.route('/book-service', methods=['POST'])
@main_bp.route('/booking', methods=['GET', 'POST'])
@login_required
def book_service():
    if request.method == 'POST':
        service_id = request.form.get('service_id')
        appt_date_str = request.form.get('date')
        appt_time = request.form.get('time', datetime.now().strftime("%I:%M %p"))

        parsed_date = date.today()
        if appt_date_str:
            try:
                parsed_date = datetime.strptime(appt_date_str, '%Y-%m-%d').date()
            except ValueError:
                parsed_date = date.today()

        new_appt = Appointment(
            user_id=current_user.id,
            client_name=current_user.name,
            phone=current_user.phone,
            email=current_user.email,
            service_id=int(service_id) if service_id else None,
            status='booked',
            payment_status='in_app',
            date=parsed_date,
            time=appt_time
        )
        db.session.add(new_appt)
        db.session.commit()
        return redirect(url_for('main.confirmation', booking_id=new_appt.id))

    return redirect(url_for('main.client_dashboard'))


@main_bp.route('/confirmation/<int:booking_id>')
@login_required
def confirmation(booking_id):
    booking = Appointment.query.get_or_404(booking_id)
    return render_template('confirmation.html', booking=booking)


@main_bp.route('/portal')
@main_bp.route('/customer-portal')
def customer_portal():
    return redirect(url_for('main.client_dashboard'))


@main_bp.route('/client-portal')
def client_portal():
    return redirect(url_for('main.client_dashboard'))


@main_bp.route('/auto-checkin/<int:booking_id>', methods=['GET', 'POST'])
def auto_checkin(booking_id):
    appt = Appointment.query.get_or_404(booking_id)
    appt.status = 'checked_in'
    db.session.commit()
    flash(f"Check-in confirmed for {appt.client_name}!", "success")
    return redirect(url_for('main.confirmation', booking_id=appt.id))


# -------------------------------------------------------------
# WALK-IN KIOSK TERMINAL
# -------------------------------------------------------------
@main_bp.route('/kiosk', methods=['GET', 'POST'])
def walkin_kiosk():
    services = Service.query.all()
    success_client = None

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        service_id = request.form.get('service_id')
        payment_method = request.form.get('payment_method', 'in_app')

        new_appt = Appointment(
            client_name=full_name,
            phone=phone,
            email=email,
            service_id=int(service_id) if service_id else None,
            status='waiting',
            payment_status=payment_method,
            date=date.today(),
            time=datetime.now().strftime("%I:%M %p")
        )
        db.session.add(new_appt)
        db.session.commit()

        position = Appointment.query.filter(
            Appointment.status.in_(['waiting', 'checked_in']),
            Appointment.date == date.today()
        ).count()

        success_client = {
            'name': full_name,
            'position': position
        }

    return render_template('kiosk.html', services=services, success_client=success_client)


# -------------------------------------------------------------
# LIVE TV DISPLAY
# -------------------------------------------------------------
@main_bp.route('/queue')
@main_bp.route('/tv')
def live_queue_display():
    today = date.today()
    active_clients = Appointment.query.filter(
        Appointment.date == today,
        Appointment.status.in_(['waiting', 'checked_in', 'in_chair'])
    ).order_by(Appointment.id.asc()).all()

    return render_template('queue_display.html', clients=active_clients)


# -------------------------------------------------------------
# STYLIST COMMAND CENTER, CSV EXPORT, ACTIONS & MANAGEMENT
# -------------------------------------------------------------
@main_bp.route('/stylist/dashboard')
@login_required
def stylist_dashboard():
    in_chair = Appointment.query.filter_by(status='in_chair').first()
    waiting_list = Appointment.query.filter(
        Appointment.status.in_(['waiting', 'checked_in', 'booked'])
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
    if current_chair and current_chair.id != appt_id:
        current_chair.status = 'completed'

    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'in_chair'
    db.session.commit()
    flash(f"{appt.client_name} is now in the chair!", "success")
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/stylist/checkout/<int:appt_id>', methods=['POST'])
@login_required
def complete_checkout(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'completed'
    db.session.commit()
    flash(f"Service completed and marked paid for {appt.client_name}.", "success")
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/stylist/add-stylist', methods=['POST'])
@login_required
def add_stylist():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', 'stylist123')

    if email and not User.query.filter_by(email=email).first():
        new_stylist = User(
            name=name,
            email=email,
            phone=phone,
            password_hash=generate_password_hash(password),
            role='stylist'
        )
        db.session.add(new_stylist)
        db.session.commit()
        flash(f"Stylist {name} added successfully!", "success")
    else:
        flash("Could not add stylist (email may already exist).", "error")

    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/stylist/add-product', methods=['POST'])
@login_required
def add_product():
    flash("Product inventory feature logged.", "info")
    return redirect(url_for('main.stylist_dashboard'))


@main_bp.route('/stylist/export-tax-csv')
@login_required
def export_tax_csv():
    completed = Appointment.query.filter_by(status='completed').all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Transaction ID', 'Date', 'Time', 'Client Name', 'Phone', 'Service', 'Price', 'Payment Method', 'Status'])

    for appt in completed:
        svc_name = appt.service.name if appt.service else 'General Haircut'
        price = f"${appt.service.price:.2f}" if (appt.service and appt.service.price) else "$35.00"
        writer.writerow([
            appt.id,
            appt.date.strftime('%Y-%m-%d') if appt.date else '',
            appt.time or '',
            appt.client_name,
            appt.phone or '',
            svc_name,
            price,
            appt.payment_status or 'in_app',
            appt.status
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=jackiecutz_tax_records.csv"}
    )


# -------------------------------------------------------------
# GEOFENCE AUTOMATIC CHECK-IN API
# -------------------------------------------------------------
@main_bp.route('/api/geofence-checkin', methods=['POST'])
def geofence_checkin():
    data = request.get_json() or {}
    user_lat = data.get('latitude') or data.get('lat')
    user_lon = data.get('longitude') or data.get('lng')
    user_identifier = data.get('user_id')

    if user_lat is None or user_lon is None:
        return jsonify({'status': 'error', 'message': 'Coordinates missing.'}), 400

    distance = calculate_haversine_distance(float(user_lat), float(user_lon), SALON_LATITUDE, SALON_LONGITUDE)

    if distance <= GEOFENCE_RADIUS_MILES:
        target_user_id = current_user.id if current_user.is_authenticated else user_identifier

        query = Appointment.query.filter(
            Appointment.date == date.today(),
            Appointment.status == 'booked'
        )
        if target_user_id:
            query = query.filter(Appointment.user_id == target_user_id)

        appt = query.first()

        if appt:
            appt.status = 'checked_in'
            db.session.commit()
            return jsonify({
                'status': 'checked_in',
                'booking_id': appt.id,
                'client_name': appt.client_name,
                'distance': round(distance, 2),
                'message': 'Welcome to Divine Salon! You have been automatically checked into the chair queue.'
            })

    return jsonify({'status': 'out_of_range', 'distance': round(distance, 2)})