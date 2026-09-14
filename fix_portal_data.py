with open('app/routes.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Route /customer_portal with full database context for booking.html
old_portal_fn = """@main_bp.route('/customer_portal')
def customer_portal():
    return render_template('booking.html')"""

new_portal_fn = """@main_bp.route('/customer_portal')
def customer_portal():
    services = ServiceCatalog.query.all()
    # Normalize price attribute so template s.price works seamlessly
    for s in services:
        s.price = getattr(s, 'price_min', 0.0)
    return render_template('booking.html', services=services)

@main_bp.route('/book_service', methods=['POST'])
def book_service():
    service_id = request.form.get('service_id')
    client_name = request.form.get('client_name', 'Client')
    client_phone = request.form.get('client_phone', '')
    booking_date = request.form.get('date', '')
    booking_time = request.form.get('time', '')
    
    svc = ServiceCatalog.query.get(service_id)
    svc_name = svc.name if svc else "Haircut Service"
    svc_price = svc.price_min if svc else 35.0
    
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
    
    flash(f"Appointment booked for {client_name}! We look forward to seeing you at Suite 105.", "success")
    return redirect(url_for('main.customer_portal'))"""

if old_portal_fn in code:
    code = code.replace(old_portal_fn, new_portal_fn)
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("Updated /customer_portal route and added /book_service endpoint!")
else:
    print("Route signature mismatched. Writing explicit replacement...")
    # Direct replacement strategy
    lines = code.split('\n')
    new_lines = []
    skip = False
    for line in lines:
        if "def customer_portal():" in line:
            new_lines.append(new_portal_fn)
            skip = True
        elif skip and line.startswith("@main_bp.route"):
            skip = False
            new_lines.append(line)
        elif not skip:
            new_lines.append(line)
    
    with open('app/routes.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    print("Replaced customer_portal function in app/routes.py!")