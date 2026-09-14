from app import create_app, db
from app.models import User, Booking, Staff, Product

app = create_app()

with app.app_context():
    print("=== WORKFLOW DIAGNOSTIC REPORT ===")
    print(f"Registered Users: {User.query.count()}")
    print(f"Registered Bookings: {Booking.query.count()}")
    print(f"Registered Staff: {Staff.query.count()}")
    
    print("\n--- APP ROUTE ENDPOINTS ---")
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint:<25} Path: {rule}")