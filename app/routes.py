import random
from datetime import datetime, timedelta
from flask_mail import Message
from app import mail

# ---------------------------------------------------------
# A. ADMIN ASSIGNS A STYLIST & SENDS 48-HR CODE
# ---------------------------------------------------------
@main_bp.route('/add_stylist', methods=['POST'])
def add_stylist():
    email = request.form.get('app_email', '').strip().lower()
    full_name = request.form.get('full_name', 'Stylist').strip()
    
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.utcnow() + timedelta(hours=48)
    
    user = User.query.filter_by(email=email).first()
    if user:
        user.invite_code = code
        user.code_expires_at = expires_at
    else:
        user = User(
            email=email,
            name=full_name,
            invite_code=code,
            code_expires_at=expires_at,
            is_stylist=False  # Upgraded upon 6-digit code verification
        )
        db.session.add(user)
        
    db.session.commit()

    try:
        msg = Message(
            subject="Jackiecutz Hair Studio - Stylist Activation Code",
            recipients=[email]
        )
        msg.body = f"""Hi {full_name},

You have been registered as a Team Member at Jackiecutz Hair Studio!

To activate your Stylist App access:
1. Visit https://jackiecutz-app.onrender.com/register
2. Register using this email address: {email}
3. Enter your 6-Digit Verification Code: {code}

*Note: This code expires in 48 hours.*

Jackiecutz Hair Studio
Divine Salon | (832) 353-4577
"""
        mail.send(msg)
        flash(f"Stylist {full_name} added! Activation code sent to {email}.", "success")
    except Exception as e:
        flash(f"Stylist added, but email failed to send: {e}", "warning")

    return redirect(url_for('main.stylist_dashboard'))


# ---------------------------------------------------------
# B. API TO CHECK IF TYPED EMAIL IS AN INVITED STYLIST
# ---------------------------------------------------------
@main_bp.route('/api/check_stylist_email', methods=['POST'])
def check_stylist_email():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    
    user = User.query.filter_by(email=email).first()
    if user and user.invite_code and user.code_expires_at:
        if datetime.utcnow() <= user.code_expires_at:
            return jsonify({'is_invited_stylist': True})
            
    return jsonify({'is_invited_stylist': False})


# ---------------------------------------------------------
# C. UPDATE REGISTER ROUTE TO PROCESS 6-DIGIT CODE
# ---------------------------------------------------------
# Inside your existing register() POST block right before saving new_user:
invite_code_submitted = request.form.get('invite_code', '').strip()
valid_stylist = False

target_user = User.query.filter_by(email=email).first()
if target_user and target_user.invite_code and target_user.code_expires_at:
    if target_user.invite_code == invite_code_submitted and datetime.utcnow() <= target_user.code_expires_at:
        valid_stylist = True

# When creating new_user:
new_user = User(
    first_name=first_name,
    last_name=last_name,
    username=username,
    name=f"{first_name} {last_name}".strip(),
    phone=phone,
    email=email,
    zip_code=zip_code,
    gender=gender,
    birthdate=birthday,
    password_hash=generate_password_hash(password),
    is_stylist=valid_stylist,
    is_admin=False  # Stylists are never given admin permissions
)


# ---------------------------------------------------------
# D. STRICT PRIVACY ROUTE ACCESS
# ---------------------------------------------------------
@main_bp.route('/dashboard')
@main_bp.route('/stylist_dashboard')
@login_required
def stylist_dashboard():
    # Block non-staff from accessing management views
    if not (getattr(current_user, 'is_admin', False) or getattr(current_user, 'is_stylist', False)):
        flash('Access restricted to salon management.', 'danger')
        return redirect(url_for('main.customer_portal'))

    # If user is a Stylist (not Admin), redirect them to their personal portal
    if getattr(current_user, 'is_stylist', False) and not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.stylist_portal', staff_id=current_user.id))

    return render_template('dashboard.html')  # Full admin overview for Ivonne


@main_bp.route('/stylist_portal/<int:staff_id>')
@login_required
def stylist_portal(staff_id):
    # Stylists can ONLY view their own personal portal unless Admin
    if current_user.id != staff_id and not getattr(current_user, 'is_admin', False):
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('main.stylist_portal', staff_id=current_user.id))

    return render_template('stylist_portal.html', staff_id=staff_id)