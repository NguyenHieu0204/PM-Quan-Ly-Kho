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
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
