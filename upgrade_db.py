import sqlite3
import os
import glob

def patch_database():
    # Locate all SQLite db files in project root and instance folder
    db_files = glob.glob('*.db') + glob.glob('instance/*.db')
    
    if not db_files:
        print("No existing .db files found. Flask will initialize the schema on startup.")
        return

    for db_path in db_files:
        print(f"Checking database schema for: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Check if 'users' table exists and check its columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(users);")
            columns = [info[1] for info in cursor.fetchall()]
            
            # Safely add is_admin column if missing
            if 'is_admin' not in columns:
                cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 1;")
                print(f"  [+] Added missing column 'is_admin' to users table in {db_path}")
            else:
                print(f"  [✓] 'is_admin' column already exists in users table in {db_path}")

        # 2. Check if 'customers' table exists and check its columns
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers';")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(customers);")
            columns = [info[1] for info in cursor.fetchall()]
            
            # Safely add username column if missing
            if 'username' not in columns:
                cursor.execute("ALTER TABLE customers ADD COLUMN username VARCHAR(80);")
                print(f"  [+] Added missing column 'username' to customers table in {db_path}")
            else:
                print(f"  [✓] 'username' column already exists in customers table in {db_path}")

        conn.commit()
        conn.close()

    print(">>> SUCCESS: Database schema upgraded in place with all existing data preserved.")

if __name__ == '__main__':
    patch_database()