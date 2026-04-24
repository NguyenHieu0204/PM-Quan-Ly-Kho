import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'inventory.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE,
        name TEXT,
        category TEXT,
        imported_price REAL,
        selling_price REAL,
        wholesale_price REAL,
        retail_price REAL,
        quantity INTEGER,
        date TEXT
    )
    ''')

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT DEFAULT 'user'
    )
    ''')

    # Create invite_codes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invite_codes (
        code TEXT PRIMARY KEY,
        is_used INTEGER DEFAULT 0,
        used_by INTEGER,
        FOREIGN KEY (used_by) REFERENCES users (id)
    )
    ''')
    
    # Insert initial invite codes if they don't exist
    initial_codes = [('WAREHOUSE2026',), ('VIP_MEMBER',), ('STARTUP_PACKAGE',)]
    cursor.executemany('INSERT OR IGNORE INTO invite_codes (code) VALUES (?)', initial_codes)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
