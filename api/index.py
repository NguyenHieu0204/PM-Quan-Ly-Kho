from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, template_folder='../templates')

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), 'inventory.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
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
def delete_product(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'message': 'Product deleted successfully'})

@app.route('/api/summary', methods=['GET'])
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
