from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='../templates')
app.secret_key = os.getenv('SECRET_KEY', 'dev_key_only_for_local_use_123')

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'inventory.db')
FIXED_INVITE_CODE = os.getenv('INVITE_CODE', 'KHO_2026')

def login_required(f):
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (data['username'],))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['password_hash'], data['password']):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'status': 'ok', 'user': {'username': user['username']}})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    # Check invite code
    if data.get('invite_code') != FIXED_INVITE_CODE:
        return jsonify({'status': 'error', 'message': 'Invalid invite code'}), 400
        
    conn = get_db()
    cursor = conn.cursor()
        
    try:
        pw_hash = generate_password_hash(data['password'])
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                      (data['username'], pw_hash))
        conn.commit()
        return jsonify({'status': 'ok'})
    except sqlite3.IntegrityError:
        return jsonify({'status': 'error', 'message': 'Username exists'}), 400
    finally:
        conn.close()

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'status': 'ok'})

@app.route('/api/auth/me', methods=['GET'])
def me():
    if 'user_id' in session:
        return jsonify({'status': 'ok', 'username': session['username']})
    return jsonify({'status': 'error'}), 401

@app.route('/api/products', methods=['GET'])
@login_required
def get_products():
    search = request.args.get('search', '').strip()
    conn = get_db()
    cursor = conn.cursor()
    
    if search:
        query = "SELECT * FROM products WHERE sku LIKE ? OR name LIKE ? ORDER BY id DESC"
        params = [f"%{search}%", f"%{search}%"]
    else:
        query = "SELECT * FROM products ORDER BY id DESC"
        params = []
        
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/products', methods=['POST'])
@login_required
def add_product():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (sku, name, category, imported_price, selling_price, 
                                 wholesale_price, retail_price, quantity, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['sku'], data['name'], data['category'], 
              float(data['imported_price']), float(data['selling_price']),
              float(data['wholesale_price']), float(data['retail_price']),
              int(data['quantity']), datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        return jsonify({'status': 'ok', 'message': 'Product added successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/products/<int:id>', methods=['PUT'])
@login_required
def update_product(id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE products SET sku=?, name=?, category=?, imported_price=?, 
                             selling_price=?, wholesale_price=?, retail_price=?, quantity=?
            WHERE id=?
        ''', (data['sku'], data['name'], data['category'], 
              float(data['imported_price']), float(data['selling_price']),
              float(data['wholesale_price']), float(data['retail_price']),
              int(data['quantity']), id))
        conn.commit()
        return jsonify({'status': 'ok', 'message': 'Product updated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/products/<int:id>', methods=['DELETE'])
@login_required
def delete_product(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'message': 'Product deleted successfully'})

@app.route('/api/summary', methods=['GET'])
@login_required
def get_summary():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT imported_price, selling_price, quantity FROM products")
    rows = cursor.fetchall()
    conn.close()
    
    total_products = len(rows)
    total_value = sum(row[0] * row[2] for row in rows)
    total_profit = sum((row[1] - row[0]) * row[2] for row in rows)
    
    return jsonify({
        'total_products': total_products,
        'total_value': total_value,
        'total_profit': total_profit
    })

if __name__ == '__main__':
    app.run(debug=True)
