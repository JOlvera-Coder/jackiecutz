from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    # Drop outdated tables to recreate schema with zip_code and city
    db.drop_all()
    db.create_all()
    
    # Add initial geographic test client records
    c1 = User(name="Maria Rodriguez", email="maria@example.com", phone="832-555-0199", zip_code="77073", city="Houston", source_channel="Mobile App")
    c2 = User(name="David Miller", email="david@example.com", phone="713-555-0144", zip_code="77090", city="Spring", source_channel="Kiosk Terminal")
    c3 = User(name="Jessica Taylor", email="jessica@example.com", phone="281-555-0188", zip_code="77067", city="North Houston", source_channel="Mobile App")
    
    db.session.add_all([c1, c2, c3])
    db.session.commit()
    print("Database rebuilt and sample client zip codes populated successfully!")