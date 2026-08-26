from datetime import datetime, date, time, timedelta
from collections import Counter
import re
import csv
import io
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response
from app import db
from app.models import (
    Customer, BarberService, BarberBooking, BookingStatus, PaymentMethod,
    User, Product, PurchaseOrder, ProductSale, StudioExpense, POStatus, ExpenseCategory
)
from app.dispatch import DispatchManager

main_bp = Blueprint('main', __name__)

def clean_phone(phone_str):
    return re.sub(r'\D', '', phone_str or '')

def get_salon_hours(target_date):
    weekday = target_date.weekday()
    if weekday in [0, 6]:
        return None, None
    elif weekday in [1, 2, 3]:
        return time(10, 0), time(18, 0)
    elif weekday in [4, 5]:
        return time(10, 0), time(19, 0)
    return None, None

@main_bp.route('/api/available-slots')
def available_slots():
    service_id = request.args.get('service_id', type=int)
    date_str = request.args.get('date')

    if not service_id or not date_str:
        return jsonify({'slots': [], 'message': 'Missing service or date.'})

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'slots': [], 'message': 'Invalid date format.'})

    start_time, end_time = get_salon_hours(target_date)
    if not start_time or not end_time:
        return jsonify({'slots': [], 'closed': True, 'message': 'Salon is closed on Sundays and Mondays.'})

    service = BarberService.query.get(service_id)
    if not service:
        return jsonify({'slots': [], 'message': 'Service not found.'})

    duration = timedelta(minutes=service.duration_minutes or 20)
    all_stylists = User.query.filter(User.role.in_(['owner', 'stylist']), User.is_active_stylist == True).all()
    qualified_stylists = [
        s for s in all_stylists 
        if service.category in s.get_specialties() or s.role == 'owner'
    ]

    if not qualified_stylists:
        return jsonify({'slots': [], 'message': 'No stylists available with specialty in ' + service.category})

    day_bookings = BarberBooking.query.filter(
        db.func.date(BarberBooking.scheduled_time) == target_date,
        BarberBooking.status.in_([BookingStatus.BOOKED, BookingStatus.WAITING, BookingStatus.IN_CHAIR])
    ).all()

    available_slots_list = []
    current_dt = datetime.combine(target_date, start_time)
    closing_dt = datetime.combine(target_date, end_time)
    now = datetime.now()
    slot_interval = timedelta(minutes=20)

    while current_dt + duration <= closing_dt:
        if target_date == now.date() and current_dt <= now + timedelta(minutes=10):
            current_dt += slot_interval
            continue

        slot_end = current_dt + duration
        free_stylist_found = False
        for stylist in qualified_stylists:
            has_collision = False
            for b in day_bookings:
                if b.stylist_id == stylist.id or b.stylist_id is None:
                    b_start = b.scheduled_time
                    b_dur = timedelta(minutes=b.service.duration_minutes if b.service else 20)
                    b_end = b_start + b_dur
                    if (current_dt < b_end) and (slot_end > b_start):
                        has_collision = True
                        break
            if not has_collision:
                free_stylist_found = True
                break

        if free_stylist_found:
            available_slots_list.append({
                'time_str': current_dt.strftime('%I:%M %p'),
                'iso_val': current_dt.strftime('%Y-%m-%dT%H:%M')
            })

        current_dt += slot_interval

    return jsonify({
        'slots': available_slots_list,
        'closed': False,
        'duration_min': service.duration_minutes,
        'total_available': len(available_slots_list)
    })

@main_bp.route('/')
def client_portal():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.login'))
    services = BarberService.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    family_members = user.get_family_members()
    return render_template('booking.html', services=services, products=products, current_user=user, family_members=family_members)

@main_bp.route('/terms')
def terms_privacy():
    return render_template('terms.html')

# --- CLIENT PROFILE & ACCOUNT MANAGEMENT ---
@main_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get_or_404(session['user_id'])
    name = request.form.get('name', '').strip()
    phone = clean_phone(request.form.get('phone', ''))
    email = request.form.get('email', '').strip().lower()
    gender = request.form.get('gender', 'Female')
    birthday = request.form.get('birthday', '').strip()
    zip_code = request.form.get('zip_code', '').strip()

    if name:
        user.name = name
        session['user_name'] = name
    if phone:
        user.phone = phone
    if email:
        user.email = email
    user.gender = gender
    user.birthday = birthday
    user.zip_code = zip_code

    if user.phone:
        cust = Customer.query.filter_by(phone=user.phone).first()
        if cust:
            cust.name = user.name
            cust.email = user.email
            cust.gender = user.gender
            cust.birthday = user.birthday
            cust.zip_code = user.zip_code

    db.session.commit()
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('main.client_portal'))

@main_bp.route('/profile/credentials', methods=['POST'])
def update_credentials():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get_or_404(session['user_id'])
    new_username = request.form.get('username', '').strip().lower()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    if new_username and new_username != user.username:
        if User.query.filter_by(username=new_username).first():
            flash('That username is already in use.', 'error')
            return redirect(url_for('main.client_portal'))
        user.username = new_username

    if new_password:
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('main.client_portal'))
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('main.client_portal'))
        user.set_password(new_password)

    db.session.commit()
    flash('Login credentials updated successfully!', 'success')
    return redirect(url_for('main.client_portal'))

@main_bp.route('/profile/family/add', methods=['POST'])
def add_family_member():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get_or_404(session['user_id'])
    name = request.form.get('family_name', '').strip()
    relationship = request.form.get('relationship', 'Child').strip()
    birthday = request.form.get('family_birthday', '').strip()

    if name:
        members = user.get_family_members()
        members.append({'name': name, 'relationship': relationship, 'birthday': birthday})
        user.set_family_members(members)
        db.session.commit()
        flash(f'Added {name} to your family list!', 'success')
    return redirect(url_for('main.client_portal'))

@main_bp.route('/profile/family/delete', methods=['POST'])
def delete_family_member():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get_or_404(session['user_id'])
    idx = request.form.get('member_index', type=int)
    members = user.get_family_members()
    if idx is not None and 0 <= idx < len(members):
        removed = members.pop(idx)
        user.set_family_members(members)
        db.session.commit()
        flash(f'Removed {removed.get("name", "member")}.', 'success')
    return redirect(url_for('main.client_portal'))

@main_bp.route('/profile/delete-account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    user = User.query.get_or_404(session['user_id'])
    if user.role == 'owner':
        flash('Owner accounts cannot be deleted.', 'error')
        return redirect(url_for('main.client_portal'))

    if user.phone:
        cust = Customer.query.filter_by(phone=user.phone).first()
        if cust:
            db.session.delete(cust)

    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash('Your account has been deleted.', 'success')
    return redirect(url_for('main.login'))

# --- STYLIST MANAGEMENT ---
@main_bp.route('/stylists/add', methods=['POST'])
def add_stylist():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    name = request.form.get('name', '').strip()
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '').strip()
    commission = request.form.get('commission_rate', type=float) or 60.0
    specialties = request.form.getlist('specialties[]')

    if not name or not username or not password:
        flash('Please fill in stylist name, username, and password.', 'error')
        return redirect(url_for('main.stylist_dashboard'))

    if User.query.filter_by(username=username).first():
        flash('That username already exists.', 'error')
        return redirect(url_for('main.stylist_dashboard'))

    new_stylist = User(
        name=name,
        username=username,
        role='stylist',
        commission_rate=commission,
        is_active_stylist=True
    )
    new_stylist.set_password(password)
    new_stylist.set_specialties(specialties)
    db.session.add(new_stylist)
    db.session.commit()
    flash(f'Added stylist {name} with {commission}% commission rate!', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/stylists/<int:stylist_id>/update', methods=['POST'])
def update_stylist_specialties(stylist_id):
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    stylist = User.query.get_or_404(stylist_id)
    specialties = request.form.getlist('specialties[]')
    commission = request.form.get('commission_rate', type=float)
    is_active = request.form.get('is_active') == 'on'
    
    stylist.set_specialties(specialties)
    if commission is not None:
        stylist.commission_rate = commission
    stylist.is_active_stylist = is_active
    db.session.commit()
    flash(f'Updated settings for {stylist.name}.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

# --- INVENTORY & PURCHASE ORDER (PO) ENGINE ---
@main_bp.route('/inventory/product/add', methods=['POST'])
def add_product():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    sku = request.form.get('sku', '').strip().upper()
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    category = request.form.get('category', 'Hair Care').strip()
    wholesale = request.form.get('wholesale_cost', type=float) or 0.00
    retail = request.form.get('retail_price', type=float) or 0.00
    stock = request.form.get('stock_qty', type=int) or 0
    image_url = request.form.get('image_url', '').strip() or "/static/img/card_bg.jpg"

    if not sku or not name:
        flash('Product SKU and Name are required.', 'error')
        return redirect(url_for('main.stylist_dashboard'))

    if Product.query.filter_by(sku=sku).first():
        flash('A product with that SKU already exists.', 'error')
        return redirect(url_for('main.stylist_dashboard'))

    prod = Product(
        sku=sku,
        name=name,
        description=description,
        category=category,
        wholesale_cost=wholesale,
        retail_price=retail,
        stock_qty=stock,
        image_url=image_url
    )
    db.session.add(prod)
    db.session.commit()
    flash(f'Added inventory item: {name} (${retail:.2f})', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/inventory/product/<int:product_id>/edit', methods=['POST'])
def edit_product(product_id):
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    prod = Product.query.get_or_404(product_id)
    prod.name = request.form.get('name', prod.name).strip()
    prod.description = request.form.get('description', prod.description).strip()
    prod.wholesale_cost = request.form.get('wholesale_cost', type=float) or prod.wholesale_cost
    prod.retail_price = request.form.get('retail_price', type=float) or prod.retail_price
    prod.stock_qty = request.form.get('stock_qty', type=int) or prod.stock_qty
    prod.image_url = request.form.get('image_url', prod.image_url).strip()

    db.session.commit()
    flash(f'Updated product {prod.name}.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/inventory/po/create', methods=['POST'])
def create_purchase_order():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    supplier = request.form.get('supplier_name', '').strip()
    product_id = request.form.get('product_id', type=int)
    qty = request.form.get('quantity', type=int) or 1
    unit_cost = request.form.get('unit_cost', type=float) or 0.00
    notes = request.form.get('notes', '').strip()

    if not supplier or not product_id or qty <= 0:
        flash('Invalid Purchase Order fields.', 'error')
        return redirect(url_for('main.stylist_dashboard'))

    po_count = PurchaseOrder.query.count() + 101
    po_num = f"PO-{po_count}"
    total = unit_cost * qty

    po = PurchaseOrder(
        po_number=po_num,
        supplier_name=supplier,
        product_id=product_id,
        quantity=qty,
        unit_cost=unit_cost,
        total_cost=total,
        status=POStatus.PENDING,
        notes=notes
    )
    db.session.add(po)
    db.session.commit()
    flash(f'Created Purchase Order {po_num} for {supplier} (${total:.2f}).', 'success')
    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/inventory/po/<int:po_id>/receive', methods=['POST'])
def receive_purchase_order(po_id):
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    po = PurchaseOrder.query.get_or_404(po_id)
    if po.status != POStatus.RECEIVED and po.status != POStatus.CLOSED:
        po.status = POStatus.RECEIVED
        po.received_at = datetime.utcnow()
        # Automatically increment product stock on reception
        po.product.stock_qty += po.quantity
        
        # Log as tax-deductible COGS supply expense
        exp = StudioExpense(
            title=f"Inventory Restock: {po.po_number} ({po.product.name})",
            category=ExpenseCategory.SUPPLIES,
            amount=po.total_cost,
            vendor=po.supplier_name,
            notes=f"Received {po.quantity} units @ ${po.unit_cost}/unit"
        )
        db.session.add(exp)
        db.session.commit()
        flash(f'Received {po.po_number}! Added {po.quantity} units to {po.product.name} stock.', 'success')

    return redirect(url_for('main.stylist_dashboard'))

@main_bp.route('/inventory/po/<int:po_id>/close', methods=['POST'])
def close_purchase_order(po_id):
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    po = PurchaseOrder.query.get_or_404(po_id)
    po.status = POStatus.CLOSED
    db.session.commit()
    flash(f'Purchase Order {po.po_number} closed out.', 'success')
    return redirect(url_for('main.stylist_dashboard'))

# --- OVERHEAD EXPENSE LOGGING ---
@main_bp.route('/expenses/add', methods=['POST'])
def add_expense():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    title = request.form.get('title', '').strip()
    category_str = request.form.get('category', 'supplies').upper()
    amount = request.form.get('amount', type=float) or 0.00
    vendor = request.form.get('vendor', '').strip()
    notes = request.form.get('notes', '').strip()

    if not title or amount <= 0:
        flash('Please enter a valid expense title and amount.', 'error')
        return redirect(url_for('main.stylist_dashboard'))

    cat_enum = ExpenseCategory.SUPPLIES
    try:
        cat_enum = ExpenseCategory[category_str]
    except KeyError:
        pass

    exp = StudioExpense(
        title=title,
        category=cat_enum,
        amount=amount,
        vendor=vendor,
        notes=notes
    )
    db.session.add(exp)
    db.session.commit()
    flash(f'Recorded overhead expense: {title} (${amount:.2f})', 'success')
    return redirect(url_for('main.stylist_dashboard'))

# --- TAX REPORT & 1-CLICK SCHEDULE C EXPORT ---
@main_bp.route('/tax/export/csv')
def export_tax_csv():
    if 'user_id' not in session or session.get('user_role') != 'owner':
        return redirect(url_for('main.login'))

    output = io.StringIO()
    writer = csv.writer(output)

    # 1. Header Information
    writer.writerow(["JACKIECUTZ HAIR STUDIO - ANNUAL TAX & FINANCIAL LEDGER"])
    writer.writerow(["Generated Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(["Business Owner", "Ivonne Gonzalez"])
    writer.writerow(["Location", "Divine Salon Suite 105, 806-E Airtex Dr, Houston, TX 77073"])
    writer.writerow([])

    # 2. Revenue Summary
    gross_services = db.session.query(db.func.sum(BarberBooking.final_amount)).filter(BarberBooking.is_paid == True).scalar() or 0.00
    gross_products = db.session.query(db.func.sum(ProductSale.total_price)).scalar() or 0.00
    gross_receipts = float(gross_services) + float(gross_products)

    total_expenses = db.session.query(db.func.sum(StudioExpense.amount)).scalar() or 0.00
    net_profit = gross_receipts - float(total_expenses)

    writer.writerow(["--- SCHEDULE C ANNUAL TAX SUMMARY ---"])
    writer.writerow(["Gross Receipts / Sales (Services)", f"${float(gross_services):.2f}"])
    writer.writerow(["Gross Retail Sales (Products)", f"${float(gross_products):.2f}"])
    writer.writerow(["TOTAL GROSS INCOME", f"${gross_receipts:.2f}"])
    writer.writerow(["Total Deductible Overhead Expenses", f"${float(total_expenses):.2f}"])
    writer.writerow(["NET TAXABLE PROFIT / LOSS", f"${net_profit:.2f}"])
    writer.writerow([])

    # 3. Itemized Deductible Expense Breakdown
    writer.writerow(["--- ITEMIZED DEDUCTIBLE EXPENSES ---"])
    writer.writerow(["Date", "Expense Category", "Title / Vendor", "Amount", "Deductible"])
    expenses = StudioExpense.query.order_by(StudioExpense.expense_date.desc()).all()
    for exp in expenses:
        writer.writerow([exp.expense_date.strftime('%Y-%m-%d'), exp.category.value.capitalize(), exp.title, f"${float(exp.amount):.2f}", "YES" if exp.is_tax_deductible else "NO"])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=Jackiecutz_Tax_Report_{datetime.now().year}.csv"}
    )

# --- MASTER COMMAND CENTER & ANALYTICS MATRIX DASHBOARD ---
@main_bp.route('/dashboard')
def stylist_dashboard():
    if 'user_id' not in session or session.get('user_role') not in ['owner', 'stylist']:
        return redirect(url_for('main.login'))

    today = date.today()
    bookings = BarberBooking.query.join(Customer).join(BarberService).filter(
        db.func.date(BarberBooking.scheduled_time) == today,
        BarberBooking.status.in_([BookingStatus.BOOKED, BookingStatus.WAITING])
    ).order_by(BarberBooking.scheduled_time.asc()).all()

    walkin_bookings = [b for b in bookings if b.status == BookingStatus.WAITING or (b.notes and 'Walk-In' in b.notes)]
    in_chair = BarberBooking.query.filter_by(status=BookingStatus.IN_CHAIR).first()
    services = BarberService.query.filter_by(is_active=True).all()
    categories = list(set([s.category for s in services]))
    stylists = User.query.filter(User.role.in_(['owner', 'stylist'])).all()
    all_customers = Customer.query.order_by(Customer.created_at.desc()).all()
    products = Product.query.order_by(Product.stock_qty.asc()).all()
    purchase_orders = PurchaseOrder.query.order_by(PurchaseOrder.created_at.desc()).all()
    expenses = StudioExpense.query.order_by(StudioExpense.expense_date.desc()).all()

    # --- ADVANCED LIVE METRICS & PIE CHART DATA ---
    # 1. Acquisition / Live Traffic Breakdown
    channels = [c.acquisition_channel or 'Direct' for c in all_customers]
    channel_counts = Counter(channels)
    chart_channel_labels = list(channel_counts.keys())
    chart_channel_data = list(channel_counts.values())

    # 2. Top Zip Codes Density
    zip_counts = Counter([c.zip_code for c in all_customers if c.zip_code])
    top_zips = zip_counts.most_common(5)
    chart_zip_labels = [z[0] for z in top_zips]
    chart_zip_data = [z[1] for z in top_zips]

    # 3. Financial Totals & Overhead
    service_revenue = db.session.query(db.func.sum(BarberBooking.final_amount)).filter(BarberBooking.is_paid == True).scalar() or 0.00
    product_revenue = db.session.query(db.func.sum(ProductSale.total_price)).scalar() or 0.00
    gross_revenue = float(service_revenue) + float(product_revenue)
    total_overhead = db.session.query(db.func.sum(StudioExpense.amount)).scalar() or 0.00
    net_income = gross_revenue - float(total_overhead)

    # 4. Stylist Performance Ledger
    stylist_matrix = []
    for st in stylists:
        st_bookings = BarberBooking.query.filter_by(stylist_id=st.id, status=BookingStatus.COMPLETED).all()
        st_sales = sum([float(b.final_amount or b.service.price) for b in st_bookings if b.is_paid])
        st_commission = st_sales * (st.commission_rate / 100.0)
        stylist_matrix.append({
            'name': st.name,
            'role': st.role,
            'rate': st.commission_rate,
            'cuts_completed': len(st_bookings),
            'gross_sales': st_sales,
            'payout_due': st_commission
        })

    return render_template(
        'dashboard.html',
        bookings=bookings,
        walkin_bookings=walkin_bookings,
        in_chair=in_chair,
        services=services,
        categories=categories,
        stylists=stylists,
        all_customers=all_customers,
        products=products,
        purchase_orders=purchase_orders,
        expenses=expenses,
        gross_revenue=gross_revenue,
        total_overhead=total_overhead,
        net_income=net_income,
        stylist_matrix=stylist_matrix,
        chart_channel_labels=chart_channel_labels,
        chart_channel_data=chart_channel_data,
        chart_zip_labels=chart_zip_labels,
        chart_zip_data=chart_zip_data,
        current_user_name=session.get('user_name')
    )

# --- BOOKING ACTIONS & DISPATCH ---
@main_bp.route('/book', methods=['POST'])
def book_service():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    primary_name = request.form.get('name', '').strip()
    primary_phone = clean_phone(request.form.get('phone', ''))
    slot_str = request.form.get('scheduled_time')
    primary_service_id = request.form.get('service_id', type=int)
    general_notes = request.form.get('notes', '').strip()
    pay_method_str = request.form.get('payment_method', 'card').upper()
    zip_code = request.form.get('zip_code', '').strip()

    if not primary_name or not primary_phone or not slot_str or not primary_service_id:
        flash('Please choose an available live slot and fill all required fields.', 'error')
        return redirect(url_for('main.client_portal'))

    scheduled_dt = datetime.fromisoformat(slot_str)
    
    pay_enum = PaymentMethod.CARD
    if pay_method_str == 'ZELLE':
        pay_enum = PaymentMethod.ZELLE
    elif pay_method_str == 'CASH_APP':
        pay_enum = PaymentMethod.CASH_APP
    elif pay_method_str == 'CASH':
        pay_enum = PaymentMethod.CASH

    primary_customer = Customer.query.filter_by(phone=primary_phone).first()
    if not primary_customer:
        primary_customer = Customer(
            name=primary_name, 
            phone=primary_phone,
            zip_code=zip_code or None
        )
        db.session.add(primary_customer)
        db.session.flush()
    else:
        primary_customer.name = primary_name
        if zip_code:
            primary_customer.zip_code = zip_code

    primary_srv = BarberService.query.get(primary_service_id)
    candidate_stylists = User.query.filter(User.role.in_(['owner', 'stylist']), User.is_active_stylist == True).all()
    assigned_stylist_id = None
    for s in candidate_stylists:
        if (primary_srv and primary_srv.category in s.get_specialties()) or s.role == 'owner':
            assigned_stylist_id = s.id
            break

    primary_booking = BarberBooking(
        customer_id=primary_customer.id,
        service_id=primary_service_id,
        stylist_id=assigned_stylist_id,
        scheduled_time=scheduled_dt,
        status=BookingStatus.BOOKED,
        payment_method=pay_enum,
        is_paid=False,
        final_amount=primary_srv.price if primary_srv else 25.00,
        notes=f"Primary Client: {primary_name}. {general_notes}".strip()
    )
    db.session.add(primary_booking)

    guest_names = request.form.getlist('guest_name[]')
    guest_services = request.form.getlist('guest_service_id[]')
    guest_times = request.form.getlist('guest_scheduled_time[]')

    for g_name, g_srv_id, g_time in zip(guest_names, guest_services, guest_times):
        g_name_clean = g_name.strip()
        if g_name_clean and g_srv_id:
            try:
                srv_id_int = int(g_srv_id)
                g_dt = datetime.fromisoformat(g_time) if g_time else scheduled_dt
                g_srv = BarberService.query.get(srv_id_int)
                g_stylist_id = None
                for s in candidate_stylists:
                    if (g_srv and g_srv.category in s.get_specialties()) or s.role == 'owner':
                        g_stylist_id = s.id
                        break

                guest_booking = BarberBooking(
                    customer_id=primary_customer.id,
                    service_id=srv_id_int,
                    stylist_id=g_stylist_id,
                    scheduled_time=g_dt,
                    status=BookingStatus.BOOKED,
                    payment_method=pay_enum,
                    is_paid=False,
                    final_amount=g_srv.price if g_srv else 25.00,
                    notes=f"Additional Guest: {g_name_clean} (Booked by {primary_name})"
                )
                db.session.add(guest_booking)
            except (ValueError, TypeError):
                continue

    db.session.commit()
    DispatchManager.notify_booking_confirmed(primary_booking)
    return redirect(url_for('main.confirmation', booking_id=primary_booking.id))

@main_bp.route('/confirmation/<int:booking_id>')
def confirmation(booking_id):
    booking = BarberBooking.query.get_or_404(booking_id)
    return render_template('confirmation.html', booking=booking)

@main_bp.route('/kiosk', methods=['GET', 'POST'])
def walkin_kiosk():
    services = BarberService.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        phone = clean_phone(request.form.get('phone', ''))
        email = request.form.get('email', '').strip().lower()
        zip_code = request.form.get('zip_code', '').strip()
        service_id = request.form.get('service_id', type=int)

        if not first_name or not last_name or not phone or not email or not service_id:
            flash('Please complete all required fields.', 'error')
            return render_template('kiosk.html', services=services, products=products)

        customer = Customer.query.filter_by(phone=phone).first()
        if not customer:
            customer = Customer(
                name=full_name,
                phone=phone,
                email=email,
                zip_code=zip_code or None,
                acquisition_channel='Salon Walk-In Kiosk'
            )
            db.session.add(customer)
            db.session.flush()
        else:
            customer.name = full_name
            customer.email = email
            if zip_code:
                customer.zip_code = zip_code

        srv = BarberService.query.get(service_id)
        walkin_booking = BarberBooking(
            customer_id=customer.id,
            service_id=service_id,
            scheduled_time=datetime.now(),
            status=BookingStatus.WAITING,
            payment_method=PaymentMethod.CASH,
            final_amount=srv.price if srv else 25.00,
            notes='Walk-In Kiosk Check-In'
        )
        db.session.add(walkin_booking)
        db.session.commit()

        DispatchManager.notify_next_in_line(walkin_booking)
        return render_template('kiosk_success.html', customer_name=full_name, email=email)

    return render_template('kiosk.html', services=services, products=products)

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            return redirect(url_for('main.client_portal'))

        flash('Invalid Username or Password', 'error')
    return render_template('login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        gender = request.form.get('gender', 'Female')
        birthday = request.form.get('birthday', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        channel = request.form.get('acquisition_channel', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone_raw = request.form.get('phone', '').strip()
        phone = clean_phone(phone_raw)
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not name or not email or not username or not password or not confirm_password or not zip_code:
            flash('All required fields must be filled out.', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'error')
            return render_template('register.html')

        new_client = User(
            name=name, 
            username=username, 
            email=email,
            phone=phone,
            gender=gender,
            birthday=birthday,
            zip_code=zip_code,
            acquisition_channel=channel,
            role='client'
        )
        new_client.set_password(password)
        db.session.add(new_client)

        if phone:
            customer = Customer.query.filter_by(phone=phone).first()
            if not customer:
                customer = Customer(
                    name=name, 
                    phone=phone, 
                    email=email, 
                    gender=gender, 
                    birthday=birthday,
                    zip_code=zip_code,
                    acquisition_channel=channel
                )
                db.session.add(customer)
            else:
                customer.email = email
                customer.gender = gender
                customer.birthday = birthday
                customer.zip_code = zip_code
                customer.acquisition_channel = channel

        db.session.commit()

        session['user_id'] = new_client.id
        session['user_name'] = new_client.name
        session['user_role'] = 'client'
        flash(f'Welcome to Jackiecutz, {name}!', 'success')
        return redirect(url_for('main.client_portal'))

    return render_template('register.html')

@main_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip().lower()
        last_name = request.form.get('last_name', '').strip().lower()
        phone = clean_phone(request.form.get('phone', ''))
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not first_name or not last_name or not phone or not new_password or not confirm_password:
            flash('Please fill in all verification fields.', 'error')
            return render_template('forgot_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('forgot_password.html')

        full_name_query = f"{first_name} {last_name}"
        user = None
        for u in User.query.all():
            u_clean = u.name.strip().lower()
            if u_clean == full_name_query or (first_name in u_clean and last_name in u_clean):
                user = u
                break

        if user:
            user.set_password(new_password)
            db.session.commit()
            flash('Password updated successfully! Please sign in.', 'success')
            return redirect(url_for('main.login'))
        else:
            flash('No matching client record found.', 'error')

    return render_template('forgot_password.html')

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))

@main_bp.route('/queue/<int:booking_id>/action', methods=['POST'])
def update_status(booking_id):
    if 'user_id' not in session or session.get('user_role') not in ['owner', 'stylist']:
        return redirect(url_for('main.login'))

    booking = BarberBooking.query.get_or_404(booking_id)
    action = request.form.get('action')

    if action == 'notify_next':
        booking.status = BookingStatus.WAITING
        DispatchManager.notify_next_in_line(booking)
    elif action == 'seat':
        BarberBooking.query.filter_by(status=BookingStatus.IN_CHAIR).update({'status': BookingStatus.COMPLETED})
        booking.status = BookingStatus.IN_CHAIR
        booking.stylist_id = session.get('user_id')
    elif action == 'checkout':
        pay_method = request.form.get('payment_method')
        booking.payment_method = PaymentMethod[pay_method.upper()] if pay_method else PaymentMethod.CASH
        booking.is_paid = True
        booking.final_amount = booking.service.price
        booking.status = BookingStatus.COMPLETED
    elif action == 'no_show_fee':
        booking.status = BookingStatus.CANCELLED
        booking.notes = f"{booking.notes or ''} [NO-SHOW FEE: $15.00]"
        booking.final_amount = 15.00
        booking.is_paid = True
        flash(f'Charged $15.00 No-Show Fee for {booking.customer.name}.', 'success')
    elif action == 'late_cancel_fee':
        booking.status = BookingStatus.CANCELLED
        booking.notes = f"{booking.notes or ''} [LATE CANCEL FEE: $10.00]"
        booking.final_amount = 10.00
        booking.is_paid = True
        flash(f'Charged $10.00 Late Cancellation Fee for {booking.customer.name}.', 'success')
    elif action == 'cancel' or action == 'waive_fee':
        booking.status = BookingStatus.CANCELLED
        booking.notes = f"{booking.notes or ''} [CANCELLED - FEE WAIVED]"
        flash(f'Appointment cancelled with fee waived for {booking.customer.name}.', 'success')

    db.session.commit()
    return redirect(url_for('main.stylist_dashboard'))