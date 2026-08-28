from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app import db
from app.models import Appointment, Service

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

        # Calculate current queue count
        queue_count = Appointment.query.filter(
            Appointment.status.in_(['waiting', 'checked_in', 'in_chair'])
        ).count()

        new_walkin = Appointment(
            client_name=client_name,
            phone=phone,
            email=email,
            service_id=int(service_id) if service_id and service_id.isdigit() else None,
            status='waiting',
            payment_status=payment_method, # 'cash' or 'in_app'
            date=datetime.utcnow().date(),
            time=datetime.utcnow().strftime("%I:%M %p")
        )

        db.session.add(new_walkin)
        db.session.commit()

        success_client = {
            'name': client_name,
            'position': queue_count + 1
        }

    services = Service.query.all() if 'Service' in globals() else []
    return render_template('kiosk.html', services=services, success_client=success_client)


# Ivonne Checkout & Complete Service Action
@main_bp.route('/stylist/complete-checkout/<int:appt_id>', methods=['POST'])
@login_required
def complete_checkout(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = 'completed'
    db.session.commit()
    flash(f"Service completed for {appt.client_name}!", "success")
    return redirect(url_for('main.stylist_dashboard'))