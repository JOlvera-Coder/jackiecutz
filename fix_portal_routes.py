with open('app/routes.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix customer_portal rendering
old_customer_route = """@main_bp.route('/customer_portal')
def customer_portal():
    return render_template('customer_app.html') if hasattr(render_template, 'customer_app') else "Customer App Active\""""

new_customer_route = """@main_bp.route('/customer_portal')
def customer_portal():
    return render_template('customer_app.html')"""

# Fix walkin_kiosk rendering
old_kiosk_route = """return render_template('kiosk.html') if hasattr(render_template, 'kiosk') else "Kiosk Active\""""
new_kiosk_route = """return render_template('kiosk.html')"""

code = code.replace(old_customer_route, new_customer_route)
code = code.replace(old_kiosk_route, new_kiosk_route)

with open('app/routes.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Fixed route render statements in app/routes.py!")