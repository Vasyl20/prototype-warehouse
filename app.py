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

    # Таблиця постачальників
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers
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
                     contact_person
                     TEXT,
                     phone
                     TEXT,
                     email
                     TEXT,
                     address
                     TEXT,
                     notes
                     TEXT,
                     created_at
                     TEXT
                     NOT
                     NULL
                 )''')

    # Таблиця клієнтів
    c.execute('''CREATE TABLE IF NOT EXISTS clients
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
                     contact_person
                     TEXT,
                     phone
                     TEXT,
                     email
                     TEXT,
                     address
                     TEXT,
                     notes
                     TEXT,
                     created_at
                     TEXT
                     NOT
                     NULL
                 )''')

    # Оновлена таблиця операцій
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
        supplier_id
        INTEGER,
        client_id
        INTEGER,
        invoice_number
        TEXT,
        notes
        TEXT,
        FOREIGN
        KEY
                 (
        product_id
                 ) REFERENCES products
                 (
                     id
                 ),
        FOREIGN KEY
                 (
                     supplier_id
                 ) REFERENCES suppliers
                 (
                     id
                 ),
        FOREIGN KEY
                 (
                     client_id
                 ) REFERENCES clients
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

    import random
    from datetime import datetime, timedelta

    # === ПОСТАЧАЛЬНИКИ ===
    suppliers_data = [
        ('ТехноПостач ТОВ', 'Іваненко Іван', '+380501234567', 'techno@example.com', 'Київ, вул. Хрещатик 1',
         'Основний постачальник електроніки'),
        ('КомпСервіс', 'Петренко Петро', '+380672345678', 'kompservice@example.com', 'Львів, вул. Городоцька 25',
         'Комп\'ютерна техніка'),
        ('ОфісПлюс', 'Сидоренко Марія', '+380933456789', 'office@example.com', 'Одеса, вул. Дерибасівська 10',
         'Офісне обладнання'),
        ('МеблСвіт', 'Коваленко Олег', '+380504567890', 'mebli@example.com', 'Харків, пр. Науки 15', 'Офісні меблі'),
        ('ЕлектроТорг', 'Бондаренко Анна', '+380675678901', 'electro@example.com', 'Дніпро, вул. Робоча 5',
         'Електротовари'),
    ]

    supplier_ids = []
    for supplier in suppliers_data:
        c.execute('''INSERT INTO suppliers
                         (name, contact_person, phone, email, address, notes, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (*supplier, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        supplier_ids.append(c.lastrowid)

    print(f"✅ Додано {len(supplier_ids)} постачальників")

    # === КЛІЄНТИ ===
    clients_data = [
        ('ТОВ "Інновація"', 'Шевченко Тарас', '+380971234567', 'innovate@example.com', 'Київ, вул. Лесі Українки 20',
         'Постійний клієнт'),
        ('ПП "БізнесГруп"', 'Мельник Олена', '+380982345678', 'business@example.com', 'Львів, вул. Франка 30',
         'Оптовий клієнт'),
        ('Фізична особа Іванов', 'Іванов Сергій', '+380633456789', 'ivanov@example.com',
         'Одеса, вул. Преображенська 45', 'Роздрібний клієнт'),
        ('ТОВ "СофтЛаб"', 'Ткаченко Дмитро', '+380504567890', 'softlab@example.com', 'Харків, вул. Сумська 100',
         'IT компанія'),
        ('ПрАТ "МегаКорп"', 'Савченко Юлія', '+380675678901', 'megacorp@example.com', 'Дніпро, пр. Гагаріна 70',
         'Великий корпоративний клієнт'),
    ]

    client_ids = []
    for client in clients_data:
        c.execute('''INSERT INTO clients
                         (name, contact_person, phone, email, address, notes, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (*client, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        client_ids.append(c.lastrowid)

    print(f"✅ Додано {len(client_ids)} клієнтів")

    # === ТОВАРИ ===
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

    locations = []
    for w in warehouses:
        for s in shelves:
            for r in racks[:3]:
                locations.append((w, s, r))
                try:
                    c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                              (w, s, r))
                except:
                    pass

    random.shuffle(locations)

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

    print(f"✅ Додано {len(product_ids)} товарів")

    # === ОПЕРАЦІЇ З ПРИВ'ЯЗКОЮ ДО ПОСТАЧАЛЬНИКІВ/КЛІЄНТІВ ===
    for product_id in product_ids:
        # Надходження від постачальників (3-4 операції)
        num_income = random.randint(3, 4)
        for _ in range(num_income):
            days_ago = random.randint(1, 30)
            op_date = datetime.now() - timedelta(days=days_ago)
            date_str = op_date.strftime('%Y-%m-%d')
            time_str = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00"

            qty = random.randint(10, 30)
            supplier_id = random.choice(supplier_ids)
            invoice_num = f"ПН-{random.randint(1000, 9999)}"

            c.execute('''INSERT INTO operations
                             (product_id, type, quantity, date, time, supplier_id, invoice_number)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (product_id, 'income', qty, date_str, time_str, supplier_id, invoice_num))

        # Відпуски клієнтам (2-3 операції)
        num_outcome = random.randint(2, 3)
        for _ in range(num_outcome):
            days_ago = random.randint(0, 25)
            op_date = datetime.now() - timedelta(days=days_ago)
            date_str = op_date.strftime('%Y-%m-%d')
            time_str = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00"

            qty = random.randint(5, 15)
            client_id = random.choice(client_ids)
            invoice_num = f"ВН-{random.randint(1000, 9999)}"

            c.execute('''INSERT INTO operations
                             (product_id, type, quantity, date, time, client_id, invoice_number)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (product_id, 'outcome', qty, date_str, time_str, client_id, invoice_num))

    print("✅ Додано операції з прив'язкою до постачальників/клієнтів")

    # === ПЕРЕМІЩЕННЯ ===
    for i in range(3):
        product_id = random.choice(product_ids)

        c.execute('''SELECT warehouse_number, shelf, rack
                     FROM products
                     WHERE id = ?''', (product_id,))
        from_loc = c.fetchone()

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

    print("✅ Додано історію переміщень")

    conn.commit()
    conn.close()

    print("\n🎉 Тестові дані успішно додано!")
    print(f"""
📊 Підсумок:
   • Постачальників: {len(supplier_ids)}
   • Клієнтів: {len(client_ids)}
   • Товарів: {len(product_ids)}
   • Операцій: ~{len(product_ids) * 6}
   • Переміщень: 3
""")

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


# ============ ПОСТАЧАЛЬНИКИ ============

@app.route('/suppliers')
@login_required
def suppliers_page():
    return render_template('suppliers.html')


@app.route('/api/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    try:
        suppliers = query_db('''SELECT id,
                                       name,
                                       contact_person,
                                       phone,
                                       email,
                                       address,
                                       notes,
                                       created_at
                                FROM suppliers
                                ORDER BY name''')
        result = [
            {
                "id": row[0],
                "name": row[1],
                "contact_person": row[2],
                "phone": row[3],
                "email": row[4],
                "address": row[5],
                "notes": row[6],
                "created_at": row[7]
            }
            for row in suppliers
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_suppliers: {e}")
        return jsonify([])


@app.route('/api/suppliers', methods=['POST'])
@login_required
def add_supplier():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        contact_person = data.get('contact_person', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        notes = data.get('notes', '').strip()

        if not name:
            return jsonify({"error": "Назва постачальника обов'язкова"}), 400

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query_db('''INSERT INTO suppliers
                        (name, contact_person, phone, email, address, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (name, contact_person, phone, email, address, notes, created_at))

        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка add_supplier: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
@login_required
def update_supplier(supplier_id):
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        contact_person = data.get('contact_person', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        notes = data.get('notes', '').strip()

        if not name:
            return jsonify({"error": "Назва постачальника обов'язкова"}), 400

        query_db('''UPDATE suppliers
                    SET name=?,
                        contact_person=?,
                        phone=?,
                        email=?,
                        address=?,
                        notes=?
                    WHERE id = ?''',
                 (name, contact_person, phone, email, address, notes, supplier_id))

        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка update_supplier: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
@login_required
def delete_supplier(supplier_id):
    try:
        # Перевіряємо чи є операції з цим постачальником
        ops = query_db("SELECT COUNT(*) FROM operations WHERE supplier_id=?", (supplier_id,), one=True)
        if ops and ops[0] > 0:
            return jsonify({"error": f"Неможливо видалити! Є {ops[0]} операцій з цим постачальником"}), 400

        query_db("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка delete_supplier: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers/<int:supplier_id>/operations', methods=['GET'])
@login_required
def get_supplier_operations(supplier_id):
    try:
        ops = query_db('''SELECT o.id,
                                 o.date,
                                 o.time,
                                 o.quantity,
                                 o.invoice_number,
                                 p.name,
                                 p.number
                          FROM operations o
                                   JOIN products p ON o.product_id = p.id
                          WHERE o.supplier_id = ?
                            AND o.type = 'income'
                          ORDER BY o.date DESC, o.time DESC''',
                       (supplier_id,))
        result = [
            {
                "id": row[0],
                "date": row[1],
                "time": row[2],
                "quantity": row[3],
                "invoice_number": row[4],
                "product_name": row[5],
                "product_number": row[6]
            }
            for row in ops
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_supplier_operations: {e}")
        return jsonify([])


# ============ КЛІЄНТИ ============

@app.route('/clients')
@login_required
def clients_page():
    return render_template('clients.html')


@app.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    try:
        clients = query_db('''SELECT id,
                                     name,
                                     contact_person,
                                     phone,
                                     email,
                                     address,
                                     notes,
                                     created_at
                              FROM clients
                              ORDER BY name''')
        result = [
            {
                "id": row[0],
                "name": row[1],
                "contact_person": row[2],
                "phone": row[3],
                "email": row[4],
                "address": row[5],
                "notes": row[6],
                "created_at": row[7]
            }
            for row in clients
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_clients: {e}")
        return jsonify([])


@app.route('/api/clients', methods=['POST'])
@login_required
def add_client():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        contact_person = data.get('contact_person', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        notes = data.get('notes', '').strip()

        if not name:
            return jsonify({"error": "Назва клієнта обов'язкова"}), 400

        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        query_db('''INSERT INTO clients
                        (name, contact_person, phone, email, address, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (name, contact_person, phone, email, address, notes, created_at))

        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка add_client: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
@login_required
def update_client(client_id):
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        contact_person = data.get('contact_person', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        notes = data.get('notes', '').strip()

        if not name:
            return jsonify({"error": "Назва клієнта обов'язкова"}), 400

        query_db('''UPDATE clients
                    SET name=?,
                        contact_person=?,
                        phone=?,
                        email=?,
                        address=?,
                        notes=?
                    WHERE id = ?''',
                 (name, contact_person, phone, email, address, notes, client_id))

        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка update_client: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
@login_required
def delete_client(client_id):
    try:
        # Перевіряємо чи є операції з цим клієнтом
        ops = query_db("SELECT COUNT(*) FROM operations WHERE client_id=?", (client_id,), one=True)
        if ops and ops[0] > 0:
            return jsonify({"error": f"Неможливо видалити! Є {ops[0]} операцій з цим клієнтом"}), 400

        query_db("DELETE FROM clients WHERE id=?", (client_id,))
        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка delete_client: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clients/<int:client_id>/operations', methods=['GET'])
@login_required
def get_client_operations(client_id):
    try:
        ops = query_db('''SELECT o.id,
                                 o.date,
                                 o.time,
                                 o.quantity,
                                 o.invoice_number,
                                 p.name,
                                 p.number
                          FROM operations o
                                   JOIN products p ON o.product_id = p.id
                          WHERE o.client_id = ?
                            AND o.type = 'outcome'
                          ORDER BY o.date DESC, o.time DESC''',
                       (client_id,))
        result = [
            {
                "id": row[0],
                "date": row[1],
                "time": row[2],
                "quantity": row[3],
                "invoice_number": row[4],
                "product_name": row[5],
                "product_number": row[6]
            }
            for row in ops
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_client_operations: {e}")
        return jsonify([])







# ============ ОПЕРАЦІЇ ============

@app.route('/api/operations', methods=['GET'])
@login_required
def get_operations():
    try:
        ops = query_db('''SELECT o.id, o.type, o.quantity, o.date, o.time, 
                                 p.name, p.number, o.invoice_number,
                                 s.name as supplier_name, c.name as client_name
                          FROM operations o
                          JOIN products p ON o.product_id = p.id
                          LEFT JOIN suppliers s ON o.supplier_id = s.id
                          LEFT JOIN clients c ON o.client_id = c.id
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
                "product_number": row[6],
                "invoice_number": row[7],
                "supplier_name": row[8],
                "client_name": row[9]
            }
            for row in ops
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_operations: {e}")
        return jsonify([])


# @app.route('/operations/income', methods=['POST'])
# @login_required
# def add_income():
#     try:
#         data = request.get_json()
#         product_id = data.get('product_id')
#         quantity = data.get('quantity')
#         date_input = data.get('date')
#         supplier_id = data.get('supplier_id')
#         invoice_number = data.get('invoice_number', '').strip()
#
#         if not product_id or not quantity or quantity <= 0:
#             return jsonify({"error": "Невірні дані"}), 400
#
#         if not supplier_id:
#             return jsonify({"error": "Виберіть постачальника"}), 400
#
#         conn = sqlite3.connect(DB_NAME)
#         c = conn.cursor()
#
#         # Перевіряємо чи існує товар
#         c.execute("SELECT id FROM products WHERE id = ?", (product_id,))
#         if not c.fetchone():
#             conn.close()
#             return jsonify({"error": "Товар не знайдено"}), 404
#
#         # Перевіряємо чи існує постачальник
#         c.execute("SELECT id FROM suppliers WHERE id = ?", (supplier_id,))
#         if not c.fetchone():
#             conn.close()
#             return jsonify({"error": "Постачальник не знайдено"}), 404
#
#         # Збільшуємо кількість
#         c.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (quantity, product_id))
#
#         # Записуємо операцію
#         now = datetime.now()
#         date_str = date_input if date_input else now.strftime('%Y-%m-%d')
#         time_str = now.strftime('%H:%M:%S')
#
#         c.execute('''INSERT INTO operations
#                          (product_id, type, quantity, date, time, supplier_id, invoice_number)
#                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
#                   (product_id, 'income', quantity, date_str, time_str, supplier_id, invoice_number))
#
#         conn.commit()
#         conn.close()
#
#         return jsonify({"success": True})
#     except Exception as e:
#         print(f"Помилка add_income: {e}")
#         return jsonify({"error": str(e)}), 500


@app.route('/operations/outcome', methods=['POST'])
@login_required
def add_outcome():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        date_input = data.get('date')
        client_id = data.get('client_id')
        invoice_number = data.get('invoice_number', '').strip()

        if not product_id or not quantity or quantity <= 0:
            return jsonify({"error": "Невірні дані"}), 400

        if not client_id:
            return jsonify({"error": "Виберіть клієнта"}), 400

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

        # Перевіряємо чи існує клієнт
        c.execute("SELECT id FROM clients WHERE id = ?", (client_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({"error": "Клієнт не знайдено"}), 404

        # Зменшуємо кількість
        c.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))

        # Записуємо операцію
        now = datetime.now()
        date_str = date_input if date_input else now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        c.execute('''INSERT INTO operations
                         (product_id, type, quantity, date, time, client_id, invoice_number)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, 'outcome', quantity, date_str, time_str, client_id, invoice_number))

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




@app.route('/operations/income', methods=['POST'])
@login_required
def add_income():
    try:
        data = request.get_json()
        quantity = data.get('quantity')
        date_input = data.get('date')
        supplier_id = data.get('supplier_id')
        invoice_number = data.get('invoice_number', '').strip()
        is_new_product = data.get('is_new_product', False)

        if not quantity or quantity <= 0:
            return jsonify({"error": "Невірна кількість"}), 400

        if not supplier_id:
            return jsonify({"error": "Виберіть постачальника"}), 400

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # Перевіряємо чи існує постачальник
        c.execute("SELECT id FROM suppliers WHERE id = ?", (supplier_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({"error": "Постачальник не знайдено"}), 404

        product_id = None

        if is_new_product:
            # === СТВОРЮЄМО НОВИЙ ТОВАР ===
            product_name = data.get('product_name', '').strip()
            product_number = data.get('product_number', '').strip()
            product_price = data.get('product_price', 0)
            warehouse_number = data.get('warehouse_number', '').strip()
            shelf = data.get('shelf', '').strip()
            rack = data.get('rack', '').strip()

            if not product_name or not warehouse_number or not shelf or not rack:
                conn.close()
                return jsonify({"error": "Заповніть всі обов'язкові поля для нового товару"}), 400

            # Додаємо локацію якщо її немає
            try:
                c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                          (warehouse_number, shelf, rack))
            except sqlite3.IntegrityError:
                pass  # Локація вже існує

            # Перевіряємо чи вільна локація
            c.execute('''SELECT id
                         FROM products
                         WHERE warehouse_number = ?
                           AND shelf = ?
                           AND rack = ?''',
                      (warehouse_number, shelf, rack))
            existing = c.fetchone()

            if existing:
                conn.close()
                return jsonify({"error": "Ця локація вже зайнята іншим товаром"}), 400

            # Створюємо новий товар з кількістю з надходження
            c.execute('''INSERT INTO products
                             (name, number, quantity, price, warehouse_number, shelf, rack)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (product_name, product_number, quantity, product_price,
                       warehouse_number, shelf, rack))

            product_id = c.lastrowid
            print(f"✅ Створено новий товар ID={product_id}")

        else:
            # === ДОДАЄМО ДО ІСНУЮЧОГО ТОВАРУ ===
            product_id = data.get('product_id')

            if not product_id:
                conn.close()
                return jsonify({"error": "Виберіть товар"}), 400

            # Перевіряємо чи існує товар
            c.execute("SELECT id FROM products WHERE id = ?", (product_id,))
            if not c.fetchone():
                conn.close()
                return jsonify({"error": "Товар не знайдено"}), 404

            # Збільшуємо кількість
            c.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?",
                      (quantity, product_id))

        # Записуємо операцію надходження
        now = datetime.now()
        date_str = date_input if date_input else now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')

        c.execute('''INSERT INTO operations
                         (product_id, type, quantity, date, time, supplier_id, invoice_number)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, 'income', quantity, date_str, time_str, supplier_id, invoice_number))

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print(f"Помилка add_income: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


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
    app.run(host='0.0.0.0', port=5000, debug=True)