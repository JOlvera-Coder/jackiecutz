import os

basedir = os.path.abspath(os.path.dirname(__file__))

# Ensure instance directory exists for SQLite
instance_dir = os.path.join(basedir, 'instance')
os.makedirs(instance_dir, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jackiecutz-secret-key-2026'
    
    # Handle Render PostgreSQL URL or fallback safely to absolute SQLite path
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    SQLALCHEMY_DATABASE_URI = db_url or f"sqlite:///{os.path.join(instance_dir, 'jackiecutz.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False