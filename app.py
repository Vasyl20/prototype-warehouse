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
    c.execute('''CREATE TABLE IF NOT EXISTS locations
    (
        warehouse_number
        TEXT
        NOT
        NULL,
        shelf
        TEXT
        NOT
        NULL,
        rack
        TEXT
        NOT
        NULL,
        PRIMARY
        KEY
                 (
        warehouse_number,
        shelf,
        rack
                 )
        )''')

    # Таблиця товарів
    c.execute('''CREATE TABLE IF NOT EXISTS products
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        name
        TEXT
        NOT
        NULL,
        number
        TEXT,
        quantity
        INTEGER
        DEFAULT
        0,
        price
        REAL,
        warehouse_number
        TEXT
        NOT
        NULL,
        shelf
        TEXT
        NOT
        NULL,
        rack
        TEXT
        NOT
        NULL,
        FOREIGN
        KEY
                 (
        warehouse_number,
        shelf,
        rack
                 )
        REFERENCES locations
                 (
                     warehouse_number,
                     shelf,
                     rack
                 )
        )''')

    # Таблиця операцій
    c.execute('''CREATE TABLE IF NOT EXISTS operations
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        product_id
        INTEGER
        NOT
        NULL,
        type
        TEXT
        NOT
        NULL,
        quantity
        INTEGER
        NOT
        NULL,
        date
        TEXT
        NOT
        NULL,
        time
        TEXT
        NOT
        NULL,
        FOREIGN
        KEY
                 (
        product_id
                 ) REFERENCES products
                 (
                     id
                 )
        )''')

    # Таблиця переміщень товарів
    c.execute('''CREATE TABLE IF NOT EXISTS movements
    (
        id
        INTEGER
        PRIMARY
        KEY
        AUTOINCREMENT,
        product_id
        INTEGER
        NOT
        NULL,
        from_warehouse
        TEXT
        NOT
        NULL,
        from_shelf
        TEXT
        NOT
        NULL,
        from_rack
        TEXT
        NOT
        NULL,
        to_warehouse
        TEXT
        NOT
        NULL,
        to_shelf
        TEXT
        NOT
        NULL,
        to_rack
        TEXT
        NOT
        NULL,
        date
        TEXT
        NOT
        NULL,
        time
        TEXT
        NOT
        NULL,
        FOREIGN
        KEY
                 (
        product_id
                 ) REFERENCES products
                 (
                     id
                 )
        )''')

    print("✅ Всі таблиці створено/перевірено")

    conn.commit()
    conn.close()


def add_sample_data():
    """Автоматичне додавання тестових даних при створенні нової БД"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Перевіряємо чи вже є дані
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] > 0:
        print("ℹ️  Дані вже існують, пропускаємо додавання зразкових даних")
        conn.close()
        return

    print("📦 Додавання тестових даних...")

    # Списки для генерації тестових даних
    product_names = [
        'Ноутбук Lenovo ThinkPad',
        'Монітор Samsung 27"',
        'Клавіатура Logitech MX Keys',
        'Миша Logitech MX Master 3',
        'Навушники Sony WH-1000XM4',
        'Принтер HP LaserJet',
        'Сканер Epson Perfection',
        'Веб-камера Logitech C920',
        'Графічний планшет Wacom',
        'Зовнішній SSD Samsung 1TB'
    ]

    warehouses = ['1', '2', '3']
    shelves = ['A', 'B', 'C', 'D']
    racks = ['1', '2', '3', '4', '5']

    # Створюємо локації
    locations = []
    for w in warehouses:
        for s in shelves:
            for r in racks[:3]:  # Беремо перші 3 стелажі
                locations.append((w, s, r))
                try:
                    c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                              (w, s, r))
                except:
                    pass

    import random
    random.shuffle(locations)

    # Додаємо 10 товарів
    product_ids = []
    for i, name in enumerate(product_names, 1):
        loc = locations[i - 1]
        number = f"ART-{1000 + i}"
        quantity = random.randint(10, 100)
        price = round(random.randint(100, 50000), 2)

        c.execute('''INSERT INTO products
                         (name, number, quantity, price, warehouse_number, shelf, rack)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (name, number, quantity, price, loc[0], loc[1], loc[2]))

        product_ids.append(c.lastrowid)

    # Додаємо операції
    from datetime import datetime, timedelta

    for product_id in product_ids:
        # Додаємо 3-5 операцій для кожного товару
        num_ops = random.randint(3, 5)
        for _ in range(num_ops):
            days_ago = random.randint(0, 30)
            op_date = datetime.now() - timedelta(days=days_ago)
            date_str = op_date.strftime('%Y-%m-%d')
            time_str = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00"

            op_type = 'income' if random.random() < 0.6 else 'outcome'
            qty = random.randint(5, 20)

            c.execute('''INSERT INTO operations
                             (product_id, type, quantity, date, time)
                         VALUES (?, ?, ?, ?, ?)''',
                      (product_id, op_type, qty, date_str, time_str))

    # Додаємо 3 переміщення
    for i in range(3):
        product_id = random.choice(product_ids)

        c.execute('''SELECT warehouse_number, shelf, rack
                     FROM products
                     WHERE id = ?''', (product_id,))
        from_loc = c.fetchone()

        # Вибираємо іншу локацію
        to_loc = random.choice([l for l in locations[:10] if l != from_loc])

        days_ago = random.randint(0, 15)
        move_date = datetime.now() - timedelta(days=days_ago)
        date_str = move_date.strftime('%Y-%m-%d')
        time_str = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00"

        c.execute('''INSERT INTO movements
                     (product_id, from_warehouse, from_shelf, from_rack,
                      to_warehouse, to_shelf, to_rack, date, time)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, from_loc[0], from_loc[1], from_loc[2],
                   to_loc[0], to_loc[1], to_loc[2], date_str, time_str))

    conn.commit()
    conn.close()

    print("✅ Додано 10 товарів з тестовими даними!")
    print("✅ Додано операції надходження/відпуску")
    print("✅ Додано історію переміщень")


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

# Роут для сторінки входу в систему
@app.route('/login')
def login_page():
    if 'logged_in' in session:
        return redirect(url_for('index'))
    return render_template('login.html')


#  API для входу в систему
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

# API для виходу з системи
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
    


# ============ РУХ ТОВАРІВ ============

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


# ============ ПЕРЕМІЩЕННЯ ТОВАРІВ ============

@app.route('/relocation')
@login_required
def relocation_page():
    return render_template('relocation.html')


@app.route('/relocation/move', methods=['POST'])
@login_required
def move_product():
    try:
        data = request.get_json()
        print(f"Отримано дані: {data}")  # Для відладки
        
        product_id = data.get('product_id')
        to_warehouse = data.get('to_warehouse')
        to_shelf = data.get('to_shelf')
        to_rack = data.get('to_rack')
        
        print(f"product_id={product_id}, to_warehouse={to_warehouse}, to_shelf={to_shelf}, to_rack={to_rack}")
        
        if not all([product_id, to_warehouse, to_shelf, to_rack]):
            print("Помилка: Не всі поля заповнені!")
            return jsonify({"error": "Заповніть всі поля!"}), 400
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Отримуємо поточну локацію товару
        c.execute('''SELECT warehouse_number, shelf, rack, name 
                     FROM products WHERE id = ?''', (product_id,))
        current = c.fetchone()
        
        if not current:
            conn.close()
            return jsonify({"error": "Товар не знайдено"}), 404
        
        from_warehouse, from_shelf, from_rack, product_name = current
        
        # Перевіряємо чи не переміщуємо в ту саму локацію
        if (from_warehouse == to_warehouse and 
            from_shelf == to_shelf and 
            from_rack == to_rack):
            conn.close()
            return jsonify({"error": "Товар вже знаходиться в цій локації!"}), 400
        
        # Перевіряємо чи вільна нова локація
        c.execute('''SELECT id FROM products 
                     WHERE warehouse_number=? AND shelf=? AND rack=?''',
                  (to_warehouse, to_shelf, to_rack))
        existing = c.fetchone()
        
        if existing:
            conn.close()
            return jsonify({"error": "Нова локація вже зайнята іншим товаром!"}), 400
        
        # Додаємо нову локацію якщо її немає
        try:
            c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                      (to_warehouse, to_shelf, to_rack))
        except sqlite3.IntegrityError:
            pass
        
        # Оновлюємо локацію товару
        c.execute('''UPDATE products 
                     SET warehouse_number=?, shelf=?, rack=? 
                     WHERE id=?''',
                  (to_warehouse, to_shelf, to_rack, product_id))
        
        # Записуємо історію переміщення
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        c.execute('''INSERT INTO movements 
                     (product_id, from_warehouse, from_shelf, from_rack, 
                      to_warehouse, to_shelf, to_rack, date, time)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, from_warehouse, from_shelf, from_rack,
                   to_warehouse, to_shelf, to_rack, date_str, time_str))
        
        conn.commit()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка move_product: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/relocation/history', methods=['GET'])
@login_required
def get_movement_history():
    try:
        movements = query_db('''SELECT m.id, m.date, m.time, 
                                       p.name, p.number,
                                       m.from_warehouse, m.from_shelf, m.from_rack,
                                       m.to_warehouse, m.to_shelf, m.to_rack
                                FROM movements m
                                JOIN products p ON m.product_id = p.id
                                ORDER BY m.date DESC, m.time DESC
                                LIMIT 50''')
        result = [
            {
                "id": row[0],
                "date": row[1],
                "time": row[2],
                "product_name": row[3],
                "product_number": row[4],
                "from_warehouse": row[5],
                "from_shelf": row[6],
                "from_rack": row[7],
                "to_warehouse": row[8],
                "to_shelf": row[9],
                "to_rack": row[10]
            }
            for row in movements
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_movement_history: {e}")
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


if __name__ == '__main__':
    # Перевіряємо чи існує база даних
    db_exists = os.path.exists(DB_NAME)

    if not db_exists:
        print("🔧 База даних не знайдена, створюємо нову...")
        init_db()
        print("✅ База даних створена!")

        # Автоматично додаємо тестові дані
        add_sample_data()
    else:
        # Якщо база існує, просто перевіряємо структуру таблиць
        init_db()

    print("🚀 Flask запущено! Відкрий у браузері: http://127.0.0.1:5000")
    print("🔐 Логін: адмін / Пароль: адмін")
    app.run(debug=True)