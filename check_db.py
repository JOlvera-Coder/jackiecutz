from app import create_app, db

print("--- DIAGNOSTIC START ---")
app = create_app()
print("SQLALCHEMY_DATABASE_URI is:", app.config.get("SQLALCHEMY_DATABASE_URI"))

with app.app_context():
    db.create_all()
    print("Database tables verified and created successfully!")
print("--- DIAGNOSTIC COMPLETE ---")