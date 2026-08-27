@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        remember = bool(request.form.get('remember_me'))
        digits = clean_phone(identifier)

        # 1. Stylist / Admin Check
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

        # 2. Universal Customer Lookup (Matches Username, Full Name, Phone, or Email)
        customer = None
        if digits and len(digits) >= 7:
            customer = Customer.query.filter(Customer.phone == digits).first()

        if not customer and hasattr(Customer, 'username'):
            customer = Customer.query.filter(Customer.username.ilike(identifier)).first()

        if not customer:
            customer = Customer.query.filter(
                (Customer.name.ilike(identifier)) |
                (Customer.name.ilike(f"%{identifier}%")) |
                (Customer.email.ilike(identifier))
            ).first()

        if customer:
            session.clear()
            session['customer_id'] = customer.id
            session.permanent = remember
            flash(f"Welcome back, {customer.name}!", "success")
            return redirect(url_for('main.customer_portal'))

        flash("Account not found or invalid credentials.", "danger")
        return redirect(url_for('main.login'))

    return render_template('login.html')