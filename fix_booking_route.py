with open('app/routes.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Route /customer_portal to booking.html instead of customer_app.html
code = code.replace("return render_template('customer_app.html')", "return render_template('booking.html')")

with open('app/routes.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Updated /customer_portal to point directly to booking.html!")