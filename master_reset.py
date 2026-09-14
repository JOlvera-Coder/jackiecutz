from app import create_app, db
from app.models import User, Booking, Staff, Product, Expense, ServiceCatalog

app = create_app()

official_menu = [
    # Men's Services (Barber)
    ("Men's", "Kids Haircut 10yr and under", 20.0, None, "Barber"),
    ("Men's", "Mens Haircut", 25.0, None, "Barber"),
    ("Men's", "Beard Detail", 10.0, None, "Barber"),
    ("Men's", "Shampoo", 5.0, None, "Barber"),
    ("Men's", "Mini Facial", 5.0, None, "Barber"),
    
    # Women's Services (Stylist)
    ("Women's", "Kids Haircut 10yr and under", 25.0, None, "Stylist"),
    ("Women's", "Women Haircut", 30.0, None, "Stylist"),
    ("Women's", "Blow Out", 30.0, 50.0, "Stylist"),
    ("Women's", "Shampoo", 10.0, None, "Stylist"),
    ("Women's", "Mini Facial", 5.0, None, "Stylist"),
    ("Women's", "Botox Hair Treatment", 100.0, 180.0, "Stylist"),
    ("Women's", "Color", 85.0, 200.0, "Stylist"),
    ("Women's", "Makeup", 45.0, 100.0, "Stylist"),
    ("Women's", "Eyelash Clusters", 25.0, None, "Stylist"),
    ("Women's", "Hairstyles", 10.0, 100.0, "Stylist"),
    
    # Wax Services (Stylist / Esthetician)
    ("Wax Services", "Eyebrows", 10.0, None, "Stylist"),
    ("Wax Services", "Lip", 7.0, None, "Stylist"),
    ("Wax Services", "Ears", 10.0, None, "Stylist"),
    ("Wax Services", "Chin", 5.0, None, "Stylist"),
]

with app.app_context():
    # Rebuild complete SQLite schema for all models
    db.drop_all()
    db.create_all()
    
    # Seed Service Catalog
    for cat, name, p_min, p_max, role in official_menu:
        svc = ServiceCatalog(category=cat, name=name, price_min=p_min, price_max=p_max, required_role=role)
        db.session.add(svc)

    # Seed Sample Geographic Clients
    c1 = User(name="Maria Rodriguez", email="maria@example.com", phone="832-555-0199", zip_code="77073", city="Houston", source_channel="Mobile App")
    c2 = User(name="David Miller", email="david@example.com", phone="713-555-0144", zip_code="77090", city="Spring", source_channel="Kiosk Terminal")
    c3 = User(name="Jessica Taylor", email="jessica@example.com", phone="281-555-0188", zip_code="77067", city="North Houston", source_channel="Mobile App")
    
    # Seed Initial Master Barber/Stylist
    s1 = Staff(name="Ivonne Gonzalez", role="Master", specialties="All Services", pay_type="Commission", pay_rate=100.0)
    
    db.session.add_all([c1, c2, c3, s1])
    db.session.commit()
    print("Master database build successful! All tables, services, and zip code clients seeded.")