import re
from datetime import datetime, date, time, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import (
    Customer, BarberService, BarberBooking, BookingStatus,
    User, Product, PurchaseOrder, ProductSale, StudioExpense
)

main_bp = Blueprint('main', __name__)

def clean_phone(phone_str):
    return re.sub(r'\D', '', phone_str or '') @main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        full_name = f"{first_name} {last_name}".strip()
        gender = request.form.get('gender', '').strip()
        birthday = request.form.get('birthday', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        zip_code = request.form.get('zip_code', '').strip()
        address = request.form.get('address', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        missing = []
        if not first_name: missing.append("First Name")
        if not last_name: missing.append("Last Name")
        if not gender: missing.append("Gender")
        if not birthday: missing.append("Birthday")
        if not email: missing.append("Email Address")
        if not phone: missing.append("Phone Number")
        if not zip_code: missing.append("Zip Code")
        if not username: missing.append("Username")
        if not password: missing.append("Password")

        if missing:
            flash(f"Please fill out: {', '.join(missing)}", "error")
            return render_template('register.html', form_data=request.form)

        cleaned = clean_phone(phone)
        existing_customer = Customer.query.filter(
            (Customer.phone == cleaned) | (Customer.email == email)
        ).first()

        if existing_customer:
            flash("An account with this phone number or email already exists. Please log in.", "error")
            return render_template('register.html', form_data=request.form)

        notes_detail = f"Zip: {zip_code}"
        if address:
            notes_detail += f" | Address: {address}"
        notes_detail += f" | Username: {username}"

        new_customer = Customer(
            name=full_name,
            phone=cleaned,
            email=email,
            gender=gender,
            birthday=birthday,
            notes=notes_detail
        )
        db.session.add(new_customer)
        db.session.commit()

        session['customer_id'] = new_customer.id
        session['customer_name'] = new_customer.name
        session['customer_phone'] = new_customer.phone

        flash(f"Welcome, {first_name}! Your account has been created.", "success")
        return redirect(url_for('main.index'))

    return render_template('register.html', form_data={})