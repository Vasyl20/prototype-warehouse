# from flask import Flask, render_template, request, jsonify
# import sqlite3
# import os

# app = Flask(__name__)
# DB_NAME = 'warehouse.db'


# def init_db():
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()

#     # Таблиця місць з комбінованим первинним ключем
#     c.execute('''CREATE TABLE IF NOT EXISTS locations (
#                     warehouse_number TEXT NOT NULL,
#                     shelf TEXT NOT NULL,
#                     rack TEXT NOT NULL,
#                     PRIMARY KEY (warehouse_number, shelf, rack)
#                 )''')

#     # Таблиця товарів з зовнішнім ключем на комбінацію полів у locations
#     c.execute('''CREATE TABLE IF NOT EXISTS products (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     name TEXT NOT NULL,
#                     number TEXT,
#                     quantity INTEGER,
#                     price REAL,
#                     warehouse_number TEXT NOT NULL,
#                     shelf TEXT NOT NULL,
#                     rack TEXT NOT NULL,
#                     FOREIGN KEY (warehouse_number, shelf, rack)
#                         REFERENCES locations (warehouse_number, shelf, rack)
#                 )''')

#     conn.commit()
#     conn.close()


# def query_db(query, args=(), one=False):
#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()
#     c.execute(query, args)
#     result = c.fetchall()
#     conn.commit()
#     conn.close()
#     return (result[0] if result else None) if one else result


# @app.route('/')
# def index():
#     return render_template('index.html')


# @app.route('/products', methods=['GET'])
# def get_products():
#     products = query_db('''SELECT id, name, number, quantity, price,
#                                   warehouse_number, shelf, rack
#                            FROM products''')
#     result = [
#         {
#             "id": row[0],
#             "name": row[1],
#             "number": row[2],
#             "quantity": row[3],
#             "price": row[4],
#             "warehouse_number": row[5],
#             "shelf": row[6],
#             "rack": row[7],
#         }
#         for row in products
#     ]
#     return jsonify(result)


# @app.route('/products', methods=['POST'])
# def add_product():
#     data = request.get_json()
#     name = data.get('name')
#     number = data.get('number')
#     quantity = data.get('quantity')
#     price = data.get('price')
#     warehouse_number = data.get('warehouse_number')
#     shelf = data.get('shelf')
#     rack = data.get('rack')

#     if not name:
#         return jsonify({"error": "Назва товару обов'язкова"}), 400

#     conn = sqlite3.connect(DB_NAME)
#     c = conn.cursor()

#     # додаємо запис у locations, якщо його ще немає
#     try:
#         c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
#                   (warehouse_number, shelf, rack))
#     except sqlite3.IntegrityError:
#         pass  # комбінація вже є

#     # перевіряємо, чи є такий товар у тій самій комбінації місця
#     c.execute('''SELECT id FROM products 
#                  WHERE warehouse_number=? AND shelf=? AND rack=?''',
#               (warehouse_number, shelf, rack))
#     existing = c.fetchone()

#     if existing:
#         conn.close()
#         return jsonify({"error": "Товар у цьому місці вже існує"}), 400

#     # додаємо товар
#     c.execute('''INSERT INTO products (name, number, quantity, price, warehouse_number, shelf, rack)
#                  VALUES (?, ?, ?, ?, ?, ?, ?)''',
#               (name, number, quantity, price, warehouse_number, shelf, rack))

#     conn.commit()
#     conn.close()
#     return jsonify({"success": True})


# @app.route('/products/<int:product_id>', methods=['PUT'])
# def update_product(product_id):
#     data = request.get_json()
#     name = data.get('name')
#     number = data.get('number')
#     quantity = data.get('quantity')
#     price = data.get('price')
#     query_db("UPDATE products SET name=?, number=?, quantity=?, price=? WHERE id=?",
#              (name, number, quantity, price, product_id))
#     return jsonify({"success": True})


# @app.route('/products/<int:product_id>', methods=['DELETE'])
# def delete_product(product_id):
#     query_db("DELETE FROM products WHERE id=?", (product_id,))
#     return jsonify({"success": True})


# if __name__ == '__main__':
#     # ⚠️ Якщо стара база існує — видаляємо, щоб не було конфліктів
#     # if os.path.exists(DB_NAME):
#     #     os.remove(DB_NAME)
#     # init_db()
#     print("🚀 Flask запущено! Відкрий у браузері: http://127.0.0.1:5000")
#     app.run(debug=True)






from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'  # Змініть на свій секретний ключ!

DB_NAME = 'warehouse.db'

# Захардкоджені дані для входу
ADMIN_USERNAME = 'адмін'
ADMIN_PASSWORD = 'адмін'


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Таблиця місць з комбінованим первинним ключем
    c.execute('''CREATE TABLE IF NOT EXISTS locations (
                    warehouse_number TEXT NOT NULL,
                    shelf TEXT NOT NULL,
                    rack TEXT NOT NULL,
                    PRIMARY KEY (warehouse_number, shelf, rack)
                )''')

    # Таблиця товарів з зовнішнім ключем на комбінацію полів у locations
    c.execute('''CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    number TEXT,
                    quantity INTEGER,
                    price REAL,
                    warehouse_number TEXT NOT NULL,
                    shelf TEXT NOT NULL,
                    rack TEXT NOT NULL,
                    FOREIGN KEY (warehouse_number, shelf, rack)
                        REFERENCES locations (warehouse_number, shelf, rack)
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


# Перевірка авторизації
def login_required(f):
    def wrapper(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


@app.route('/login')
def login_page():
    # Якщо вже залогінений - перенаправляємо на головну
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


@app.route('/')
@login_required
def index():
    return render_template('index.html')


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
    quantity = data.get('quantity')
    price = data.get('price')
    warehouse_number = data.get('warehouse_number')
    shelf = data.get('shelf')
    rack = data.get('rack')

    if not name:
        return jsonify({"error": "Назва товару обов'язкова"}), 400

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # додаємо запис у locations, якщо його ще немає
    try:
        c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                  (warehouse_number, shelf, rack))
    except sqlite3.IntegrityError:
        pass  # комбінація вже є

    # перевіряємо, чи є такий товар у тій самій комбінації місця
    c.execute('''SELECT id FROM products 
                 WHERE warehouse_number=? AND shelf=? AND rack=?''',
              (warehouse_number, shelf, rack))
    existing = c.fetchone()

    if existing:
        conn.close()
        return jsonify({"error": "Товар у цьому місці вже існує"}), 400

    # додаємо товар
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


if __name__ == '__main__':
    if not os.path.exists(DB_NAME):
        init_db()
    print("🚀 Flask запущено! Відкрий у браузері: http://127.0.0.1:5000")
    print("🔐 Логін: адмін / Пароль: адмін")
    app.run(debug=True)