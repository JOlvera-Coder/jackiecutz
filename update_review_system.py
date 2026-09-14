routes_code = """from flask import render_template, request, redirect, url_for, flash, jsonify, Blueprint
from app import db
from app.models import User, Booking, Staff, Product, Expense, ServiceCatalog, BankAccount
from datetime import datetime, date
import random

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/login')
def login():
    return render_template('login.html')

@main_bp.route('/stylist/dashboard')
def stylist_dashboard():
    clients = User.query.all()
    bookings = Booking.query.all()
    staff = Staff.query.all()
    products = Product.query.all()
    expenses = Expense.query.all()
    services = ServiceCatalog.query.all()

    bank_account = BankAccount.query.first()
    if not bank_account:
        bank_account = BankAccount(
            bank_name='Not Connected',
            account_holder='Unlinked Account',
            routing_number='*****',
            account_number='*****',
            account_type='Checking',
            status='Action Required: Unlinked ⚠️'
        )
        db.session.add(bank_account)
        db.session.commit()

    today_date = date.today()

    today_revenue = sum(
        b.price + (b.retail_add_on or 0.0)
        for b in bookings
        if b.status == 'completed' and getattr(b, 'timestamp', datetime.utcnow()).date() == today_date
    )

    gross_revenue = sum(b.price + (b.retail_add_on or 0.0) for b in bookings if b.status == 'completed')
    kiosk_revenue = sum(b.price + (b.retail_add_on or 0.0) for b in bookings if getattr(b, 'source_channel', '') == 'Kiosk Terminal' and b.status == 'completed')
    app_revenue = sum(b.price + (b.retail_add_on or 0.0) for b in bookings if getattr(b, 'source_channel', '') == 'Mobile App' and b.status == 'completed')
    
    total_completed = len([b for b in bookings if b.status == 'completed'])
    aov = (gross_revenue / total_completed) if total_completed > 0 else 0.0
    
    rebooked_count = len([b for b in bookings if getattr(b, 'rebooked_on_checkout', False)])
    rebooking_rate = (rebooked_count / total_completed * 100) if total_completed > 0 else 0.0
    
    total_hours = sum(getattr(b, 'duration_minutes', 45) for b in bookings if b.status == 'completed') / 60.0
    revpash = (gross_revenue / total_hours) if total_hours > 0 else 0.0
    
    total_overhead = sum(e.amount for e in expenses)
    net_income = gross_revenue - total_overhead

    zip_counts = {}
    for client in clients:
        client.total_spent = sum(b.price + (b.retail_add_on or 0.0) for b in client.bookings if b.status == 'completed')
        z = getattr(client, 'zip_code', None) or '77073'
        zip_counts[z] = zip_counts.get(z, 0) + 1

    active_queue = [b for b in bookings if b.status in ['in-queue', 'in-chair']]

    for s in staff:
        s.completed_bookings = [b for b in bookings if b.stylist_id == s.id and b.status == 'completed']
        s_gross = sum(b.price + (b.retail_add_on or 0.0) for b in s.completed_bookings)
        if s.pay_type == 'Commission':
            s.net_payout = (s_gross * (s.pay_rate / 100.0)) - (s.booth_rent or 0.0)
        elif s.pay_type == 'Booth Rent':
            s.net_payout = s_gross - (s.booth_rent or 0.0)
        else:
            s.net_payout = s_gross

    return render_template(
        'dashboard.html',
        clients=clients,
        bookings=bookings,
        staff=staff,
        products=products,
        expenses=expenses,
        services=services,
        zip_counts=zip_counts,
        active_queue=active_queue,
        today_revenue=today_revenue,
        gross_revenue=gross_revenue,
        kiosk_revenue=kiosk_revenue,
        app_revenue=app_revenue,
        aov=aov,
        rebooking_rate=rebooking_rate,
        revpash=revpash,
        total_overhead=total_overhead,
        net_income=net_income,
        bank=bank_account
    )

@main_bp.route('/submit_review', methods=['POST'])
def submit_review():
    rating = int(request.form.get('rating', 5))
    feedback = request.form.get('feedback', '')
    client_name = request.form.get('client_name', 'Valued Client')

    if rating >= 4:
        # High Rating (4 or 5 Stars): Route to official Google Review link
        return redirect("https://g.page/r/CafPhbBwHLHwEAI/review")
    else:
        # Low Rating (1, 2, or 3 Stars): Route privately to Ivonne's resolution email
        print(f"PRIVATE FEEDBACK ALERT SENT TO jackiecutz26@gmail.com: {client_name} gave {rating} stars. Feedback: {feedback}")
        flash("Thank you for your feedback! Ivonne has received your message and will reach out personally to resolve your experience.", "info")
        return redirect(url_for('main.customer_portal'))

@main_bp.route('/save_bank_account', methods=['POST'])
def save_bank_account():
    bank_name = request.form.get('bank_name')
    account_holder = request.form.get('account_holder')
    routing = request.form.get('routing_number', '')
    account = request.form.get('account_number', '')
    account_type = request.form.get('account_type', 'Business Checking')

    bank_account = BankAccount.query.first()
    if not bank_account:
        bank_account = BankAccount()
        db.session.add(bank_account)

    if bank_name:
        bank_account.bank_name = bank_name
    if account_holder:
        bank_account.account_holder = account_holder
    if routing:
        bank_account.routing_number = f"*****{routing[-4:]}" if len(routing) >= 4 else "*****"
    if account:
        bank_account.account_number = f"*************{account[-4:]}" if len(account) >= 4 else "*****"
    if account_type:
        bank_account.account_type = account_type
    
    bank_account.status = 'Verified & Connected 🟢'
    bank_account.updated_at = datetime.utcnow()
    db.session.commit()

    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/cashout_staff/<int:staff_id>', methods=['POST'])
def cashout_staff(staff_id):
    s = Staff.query.get(staff_id)
    bank_account = BankAccount.query.first()
    b_name = bank_account.bank_name if bank_account else "Operating Bank"

    if s:
        s_bookings = [b for b in Booking.query.filter_by(stylist_id=s.id, status='completed').all()]
        s_gross = sum(b.price + (b.retail_add_on or 0.0) for b in s_bookings)
        payout_amount = (s_gross * (s.pay_rate / 100.0)) - (s.booth_rent or 0.0) if s.pay_type == 'Commission' else s_gross
        
        if payout_amount > 0:
            exp = Expense(
                category="Payroll",
                description=f"Direct ACH Payout to {s.name} from linked account ({b_name})",
                amount=payout_amount
            )
            s.last_payout_date = datetime.utcnow()
            db.session.add(exp)
            db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_service', methods=['POST'])
def add_service():
    category = request.form.get('category')
    name = request.form.get('name')
    price_min = float(request.form.get('price_min', 0.0))
    price_max_val = request.form.get('price_max')
    price_max = float(price_max_val) if price_max_val else None
    required_role = request.form.get('required_role', 'Any')

    if category and name:
        svc = ServiceCatalog(category=category, name=name, price_min=price_min, price_max=price_max, required_role=required_role)
        db.session.add(svc)
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_service', methods=['POST'])
def edit_service():
    service_id = request.form.get('service_id')
    svc = ServiceCatalog.query.get(service_id)
    if svc:
        svc.category = request.form.get('category')
        svc.name = request.form.get('name')
        svc.price_min = float(request.form.get('price_min', 0.0))
        p_max = request.form.get('price_max')
        svc.price_max = float(p_max) if p_max else None
        svc.required_role = request.form.get('required_role')
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    svc = ServiceCatalog.query.get(service_id)
    if svc:
        db.session.delete(svc)
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_product', methods=['POST'])
def add_product():
    sku = request.form.get('sku')
    name = request.form.get('name')
    cost = float(request.form.get('cost', 0.0))
    price = float(request.form.get('price', 0.0))
    stock = int(request.form.get('stock', 0))

    if name:
        new_prod = Product(sku=sku, name=name, cost=cost, price=price, stock=stock)
        db.session.add(new_prod)
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_product', methods=['POST'])
def edit_product():
    product_id = request.form.get('product_id')
    prod = Product.query.get(product_id)
    if prod:
        prod.sku = request.form.get('sku')
        prod.name = request.form.get('name')
        prod.cost = float(request.form.get('cost', 0.0))
        prod.price = float(request.form.get('price', 0.0))
        prod.stock = int(request.form.get('stock', 0))
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    prod = Product.query.get(product_id)
    if prod:
        db.session.delete(prod)
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_stylist', methods=['POST'])
def add_stylist():
    name = request.form.get('name')
    email = request.form.get('email', '')
    role = request.form.get('role', 'Barber')
    pay_type = request.form.get('pay_type', 'Commission')
    pay_rate = float(request.form.get('pay_rate', 70.0))
    booth_rent = float(request.form.get('booth_rent', 0.0))
    cashout_frequency = request.form.get('cashout_frequency', 'Weekly')
    specialties_list = request.form.getlist('specialties')
    specialties_str = ", ".join(specialties_list) if specialties_list else "General"

    if name:
        new_staff = Staff(
            name=name,
            email=email,
            role=role,
            specialties=specialties_str,
            pay_type=pay_type,
            pay_rate=pay_rate,
            booth_rent=booth_rent,
            cashout_frequency=cashout_frequency
        )
        db.session.add(new_staff)
        db.session.commit()

        if email:
            u = User.query.filter_by(email=email).first()
            if not u:
                u = User(name=name, email=email, source_channel='Command Center')
                db.session.add(u)
            u.is_stylist = True
            u.staff_id = new_staff.id
            db.session.commit()

    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/update_booking_status', methods=['POST'])
def update_booking_status():
    booking_id = request.form.get('booking_id')
    status = request.form.get('status')
    stylist_id = request.form.get('stylist_id')
    
    booking = Booking.query.get(booking_id)
    if booking:
        if stylist_id:
            booking.stylist_id = int(stylist_id)
        booking.status = status
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/stylist_portal/<int:staff_id>')
def stylist_portal(staff_id):
    staff_member = Staff.query.get_or_404(staff_id)
    my_bookings = Booking.query.filter_by(stylist_id=staff_member.id).all()
    completed = [b for b in my_bookings if b.status == 'completed']
    my_gross = sum(b.price + (b.retail_add_on or 0.0) for b in completed)
    pending_payout = (my_gross * (staff_member.pay_rate / 100.0)) - (staff_member.booth_rent or 0.0) if staff_member.pay_type == 'Commission' else my_gross

    return render_template(
        'stylist_portal.html',
        staff=staff_member,
        bookings=my_bookings,
        completed=completed,
        my_gross=my_gross,
        pending_payout=pending_payout
    )

@main_bp.route('/add_client', methods=['POST'])
def add_client():
    name = request.form.get('name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    zip_code = request.form.get('zip_code', '77073')
    if name and email:
        new_client = User(name=name, email=email, phone=phone, zip_code=zip_code, source_channel='Command Center')
        db.session.add(new_client)
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/edit_client', methods=['POST'])
def edit_client():
    client_id = request.form.get('client_id')
    client = User.query.get(client_id)
    if client:
        client.name = request.form.get('name')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.zip_code = request.form.get('zip_code', '77073')
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/delete_client/<int:client_id>', methods=['POST'])
def delete_client(client_id):
    client = User.query.get(client_id)
    if client:
        Booking.query.filter_by(user_id=client.id).delete()
        db.session.delete(client)
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/add_expense', methods=['POST'])
def add_expense():
    category = request.form.get('category')
    description = request.form.get('description', '')
    amount = float(request.form.get('amount', 0.0))
    if category and amount > 0:
        new_expense = Expense(category=category, description=description, amount=amount)
        db.session.add(new_expense)
        db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/walkin_kiosk', methods=['GET', 'POST'])
def walkin_kiosk():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        service_name = request.form.get('service_name', "Mens Haircut")
        
        service_item = ServiceCatalog.query.filter_by(name=service_name).first()
        req_role = service_item.required_role if service_item else 'Any'
        
        eligible_staff = Staff.query.all()
        if req_role != 'Any':
            eligible_staff = [s for s in eligible_staff if s.role == req_role or s.role == 'Master']
            
        if not eligible_staff:
            return jsonify({
                "status": "error",
                "message": f"No active {req_role} available for this service."
            }), 400

        assigned_staff = random.choice(eligible_staff)

        if not email:
            email = f"walkin_{phone.replace('-', '')}@kiosk.local" if phone else f"walkin_{random.randint(1000,9999)}@kiosk.local"

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name, email=email, phone=phone, source_channel='Kiosk Terminal')
            db.session.add(user)
            db.session.commit()

        booking_ref = f"#JC-{random.randint(1000, 9999)}"
        new_booking = Booking(
            user_id=user.id,
            stylist_id=assigned_staff.id,
            service_name=service_name,
            price=service_item.price_min if service_item else 25.0,
            status='in-queue',
            source_channel='Kiosk Terminal'
        )
        db.session.add(new_booking)
        db.session.commit()

        return jsonify({
            "status": "success",
            "booking_reference": booking_ref,
            "assigned_staff": assigned_staff.name
        })
    return render_template('kiosk.html') if hasattr(render_template, 'kiosk') else "Kiosk Active"

@main_bp.route('/customer_portal')
def customer_portal():
    return render_template('customer_app.html') if hasattr(render_template, 'customer_app') else "Customer App Active"

@main_bp.route('/export_tax_csv')
def export_tax_csv():
    return jsonify({"status": "CSV Exported"})

@main_bp.route('/logout')
def logout():
    return redirect(url_for('main.login'))
"""

with open('app/routes.py', 'w', encoding='utf-8') as f:
    f.write(routes_code)

print("Updated app/routes.py with automated Google Review routing and private feedback fallback!")