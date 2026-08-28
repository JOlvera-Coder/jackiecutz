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

        # Count active people ahead in line
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

    try:
        services = Service.query.all()
    except Exception:
        services = []

    return render_template('kiosk.html', services=services, success_client=success_client)


@main_bp.route('/queue')
@main_bp.route('/tv')
def live_queue_display():
    try:
        in_chair = Appointment.query.filter_by(status='in_chair').first()
        waiting_list = Appointment.query.filter(
            Appointment.status.in_(['waiting', 'checked_in'])
        ).order_by(Appointment.id.asc()).all()
    except Exception:
        in_chair = None
        waiting_list = []

    return render_template(
        'queue_display.html',
        in_chair=in_chair,
        waiting_list=waiting_list,
        total_waiting=len(waiting_list)
    )