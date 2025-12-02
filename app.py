from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

DB_NAME = 'warehouse.db'

# Захардкоджені дані для входу
ADMIN_USERNAME = 'адмін'
ADMIN_PASSWORD = 'адмін'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Таблиця місць
    c.execute('''CREATE TABLE IF NOT EXISTS locations (
                    warehouse_number TEXT NOT NULL,
                    shelf TEXT NOT NULL,
                    rack TEXT NOT NULL,
                    PRIMARY KEY (warehouse_number, shelf, rack)
                )''')

    # Таблиця товарів
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    number TEXT,
                    quantity INTEGER DEFAULT 0,
                    price REAL,
                    warehouse_number TEXT NOT NULL,
                    shelf TEXT NOT NULL,
                    rack TEXT NOT NULL,
                    FOREIGN KEY (warehouse_number, shelf, rack)
                        REFERENCES locations (warehouse_number, shelf, rack)
                )''')

    # Таблиця операцій
    c.execute('''CREATE TABLE IF NOT EXISTS operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )''')

    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(query, args)
    result = c.fetchall()
    conn.commit()
    conn.close()
    return (result[0] if result else None) if one else result


# Декоратор авторизації
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


# ============ АВТОРИЗАЦІЯ ============

@app.route('/login')
def login_page():
    if 'logged_in' in session:
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True
        session['username'] = username
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Невірний логін або пароль"}), 401


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


# ============ ГОЛОВНА СТОРІНКА ============

@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/stock')
@login_required
def stock_page():
    return render_template('stock.html')


@app.route('/operations')
@login_required
def operations_page():
    return render_template('operations.html')


# ============ ТОВАРИ ============

@app.route('/products', methods=['GET'])
@login_required
def get_products():
    products = query_db('''SELECT id, name, number, quantity, price,
                                  warehouse_number, shelf, rack
                           FROM products''')
    result = [
        {
            "id": row[0],
            "name": row[1],
            "number": row[2],
            "quantity": row[3],
            "price": row[4],
            "warehouse_number": row[5],
            "shelf": row[6],
            "rack": row[7],
        }
        for row in products
    ]
    return jsonify(result)


@app.route('/products', methods=['POST'])
@login_required
def add_product():
    data = request.get_json()
    name = data.get('name')
    number = data.get('number')
    quantity = data.get('quantity', 0)
    price = data.get('price')
    warehouse_number = data.get('warehouse_number')
    shelf = data.get('shelf')
    rack = data.get('rack')

    if not name:
        return jsonify({"error": "Назва товару обов'язкова"}), 400

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Додаємо локацію якщо її немає
    try:
        c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                  (warehouse_number, shelf, rack))
    except sqlite3.IntegrityError:
        pass

    # Перевіряємо чи є товар на цій локації
    c.execute('''SELECT id FROM products 
                 WHERE warehouse_number=? AND shelf=? AND rack=?''',
              (warehouse_number, shelf, rack))
    existing = c.fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "Товар у цьому місці вже існує"}), 400

    # Додаємо товар
    c.execute('''INSERT INTO products (name, number, quantity, price, warehouse_number, shelf, rack)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (name, number, quantity, price, warehouse_number, shelf, rack))

    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route('/products/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    data = request.get_json()
    name = data.get('name')
    number = data.get('number')
    quantity = data.get('quantity')
    price = data.get('price')
    query_db("UPDATE products SET name=?, number=?, quantity=?, price=? WHERE id=?",
             (name, number, quantity, price, product_id))
    return jsonify({"success": True})


@app.route('/products/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    query_db("DELETE FROM products WHERE id=?", (product_id,))
    return jsonify({"success": True})


# ============ ОПЕРАЦІЇ ============

@app.route('/api/operations', methods=['GET'])
@login_required
def get_operations():
    try:
        ops = query_db('''SELECT o.id, o.type, o.quantity, o.date, o.time, p.name, p.number
                          FROM operations o
                          JOIN products p ON o.product_id = p.id
                          ORDER BY o.date DESC, o.time DESC
                          LIMIT 20''')
        result = [
            {
                "id": row[0],
                "type": row[1],
                "quantity": row[2],
                "date": row[3],
                "time": row[4],
                "product_name": row[5],
                "product_number": row[6]
            }
            for row in ops
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_operations: {e}")
        return jsonify([])


@app.route('/operations/income', methods=['POST'])
@login_required
def add_income():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        date_input = data.get('date')
        
        if not product_id or not quantity or quantity <= 0:
            return jsonify({"error": "Невірні дані"}), 400
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Перевіряємо чи існує товар
        c.execute("SELECT id FROM products WHERE id = ?", (product_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({"error": "Товар не знайдено"}), 404
        
        # Збільшуємо кількість
        c.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (quantity, product_id))
        
        # Записуємо операцію
        now = datetime.now()
        date_str = date_input if date_input else now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        c.execute("INSERT INTO operations (product_id, type, quantity, date, time) VALUES (?, ?, ?, ?, ?)",
                  (product_id, 'income', quantity, date_str, time_str))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка add_income: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/operations/outcome', methods=['POST'])
@login_required
def add_outcome():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        date_input = data.get('date')
        
        if not product_id or not quantity or quantity <= 0:
            return jsonify({"error": "Невірні дані"}), 400
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Перевіряємо наявність товару
        c.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
        result = c.fetchone()
        
        if not result:
            conn.close()
            return jsonify({"error": "Товар не знайдено"}), 404
        
        if result[0] < quantity:
            conn.close()
            return jsonify({"error": f"Недостатньо товару на складі. Доступно: {result[0]}"}), 400
        
        # Зменшуємо кількість
        c.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))
        
        # Записуємо операцію
        now = datetime.now()
        date_str = date_input if date_input else now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        c.execute("INSERT INTO operations (product_id, type, quantity, date, time) VALUES (?, ?, ?, ?, ?)",
                  (product_id, 'outcome', quantity, date_str, time_str))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка add_outcome: {e}")
        return jsonify({"error": str(e)}), 500
    






#  РУХУ ТОВАРІВ ============

@app.route('/movement')
@login_required
def movement_page():
    return render_template('movement.html')


# API для отримання ВСІХ операцій (для сторінки руху товарів)
@app.route('/api/operations/all', methods=['GET'])
@login_required
def get_all_operations():
    try:
        ops = query_db('''SELECT o.id, o.type, o.quantity, o.date, o.time, p.name, p.number
                          FROM operations o
                          JOIN products p ON o.product_id = p.id
                          ORDER BY o.date DESC, o.time DESC''')
        result = [
            {
                "id": row[0],
                "type": row[1],
                "quantity": row[2],
                "date": row[3],
                "time": row[4],
                "product_name": row[5],
                "product_number": row[6]
            }
            for row in ops
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_all_operations: {e}")
        return jsonify([])






# ============ DASHBOARD ============

# 1. Роут для сторінки дашборду
@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html')


# 2. API для операцій за сьогодні
@app.route('/api/operations/today', methods=['GET'])
@login_required
def get_today_operations():
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        ops = query_db('''SELECT o.id, o.type, o.quantity, o.date, o.time, p.name, p.number
                          FROM operations o
                          JOIN products p ON o.product_id = p.id
                          WHERE o.date = ?
                          ORDER BY o.time DESC''', (today,))
        result = [
            {
                "id": row[0],
                "type": row[1],
                "quantity": row[2],
                "date": row[3],
                "time": row[4],
                "product_name": row[5],
                "product_number": row[6]
            }
            for row in ops
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_today_operations: {e}")
        return jsonify([])


# # 3. API для всіх операцій (для графіків)
# @app.route('/api/operations/all', methods=['GET'])
# @login_required
# def get_all_operations():
#     try:
#         ops = query_db('''SELECT o.id, o.type, o.quantity, o.date, o.time, p.name, p.number
#                           FROM operations o
#                           JOIN products p ON o.product_id = p.id
#                           ORDER BY o.date DESC, o.time DESC''')
#         result = [
#             {
#                 "id": row[0],
#                 "type": row[1],
#                 "quantity": row[2],
#                 "date": row[3],
#                 "time": row[4],
#                 "product_name": row[5],
#                 "product_number": row[6]
#             }
#             for row in ops
#         ]
#         return jsonify(result)
#     except Exception as e:
#         print(f"Помилка get_all_operations: {e}")
#         return jsonify([])





if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        init_db()
        print("✅ База даних створена!")
    print("🚀 Flask запущено! Відкрий у браузері: http://127.0.0.1:5000")
    print("🔐 Логін: адмін / Пароль: адмін")
    app.run(debug=True)