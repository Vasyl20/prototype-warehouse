# ============================================================================
# СИСТЕМА УПРАВЛІННЯ СКЛАДОМ - Flask Backend
# ============================================================================
# Цей файл містить повний бекенд для веб-додатку управління складом.
# Основні функції: облік товарів, операції надходження/відпуску,
# управління постачальниками/клієнтами, переміщення товарів між локаціями.
# ============================================================================

# --- ІМПОРТ БІБЛІОТЕК ---
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3  # Для роботи з базою даних SQLite
import os  # Для перевірки існування файлів
from datetime import datetime  # Для роботи з датами та часом

# --- ІНІЦІАЛІЗАЦІЯ ДОДАТКУ ---
app = Flask(__name__)  # Створюємо Flask-додаток
app.secret_key = 'your-secret-key-here-change-in-production'  # Секретний ключ для сесій (ОБОВ'ЯЗКОВО змінити у продакшені!)

# --- КОНСТАНТИ ---
DB_NAME = 'warehouse.db'  # Назва файлу бази даних SQLite

# Дані для входу в систему (захардкоджені для простоти)
ADMIN_USERNAME = 'адмін'  # Логін адміністратора
ADMIN_PASSWORD = 'адмін'  # Пароль адміністратора


# ============================================================================
# ФУНКЦІЯ ІНІЦІАЛІЗАЦІЇ БАЗИ ДАНИХ
# ============================================================================
def init_db():
    """
    Створює всі необхідні таблиці в базі даних, якщо їх ще немає.
    Викликається при першому запуску або для перевірки структури БД.
    """
    # Підключаємося до бази даних (файл створюється автоматично, якщо не існує)
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()  # Створюємо курсор для виконання SQL-запитів

    # --- ТАБЛИЦЯ МІСЦЬ (ЛОКАЦІЙ) НА СКЛАДІ ---
    # Зберігає всі можливі локації: склад → стелаж → полиця
    c.execute('''CREATE TABLE IF NOT EXISTS locations
    (
        warehouse_number TEXT NOT NULL,  -- Номер складу (наприклад: "1", "2", "3")
        shelf TEXT NOT NULL,             -- Номер стелажу (наприклад: "A", "B", "C")
        rack TEXT NOT NULL,              -- Номер полиці (наприклад: "1", "2", "3")
        PRIMARY KEY (warehouse_number, shelf, rack)  -- Комбінація цих трьох полів унікальна
    )''')

    # --- ТАБЛИЦЯ ТОВАРІВ ---
    # Основна таблиця з інформацією про всі товари на складі
    c.execute('''CREATE TABLE IF NOT EXISTS products
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Унікальний ID товару (генерується автоматично)
        name TEXT NOT NULL,                    -- Назва товару (обов'язкове поле)
        number TEXT,                           -- Артикул/номер товару (необов'язково)
        quantity INTEGER DEFAULT 0,            -- Кількість товару на складі (за замовчуванням 0)
        price REAL,                            -- Ціна товару (може бути NULL)
        warehouse_number TEXT NOT NULL,        -- Номер складу, де зберігається товар
        shelf TEXT NOT NULL,                   -- Стелаж, де зберігається товар
        rack TEXT NOT NULL,                    -- Полиця, де зберігається товар
        FOREIGN KEY (warehouse_number, shelf, rack)  -- Зв'язок з таблицею locations
            REFERENCES locations (warehouse_number, shelf, rack)
    )''')

    # --- ТАБЛИЦЯ ПОСТАЧАЛЬНИКІВ ---
    # Зберігає інформацію про компанії/осіб, які постачають товари
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers
                 (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Унікальний ID постачальника
                     name TEXT NOT NULL,                    -- Назва компанії/ПІБ (обов'язково)
                     contact_person TEXT,                   -- Контактна особа
                     phone TEXT,                            -- Телефон
                     email TEXT,                            -- Email
                     address TEXT,                          -- Адреса
                     notes TEXT,                            -- Додаткові примітки
                     created_at TEXT NOT NULL               -- Дата та час створення запису
                 )''')

    # --- ТАБЛИЦЯ КЛІЄНТІВ ---
    # Зберігає інформацію про покупців/компанії, яким відпускаємо товар
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Унікальний ID клієнта
                     name TEXT NOT NULL,                    -- Назва компанії/ПІБ (обов'язково)
                     contact_person TEXT,                   -- Контактна особа
                     phone TEXT,                            -- Телефон
                     email TEXT,                            -- Email
                     address TEXT,                          -- Адреса
                     notes TEXT,                            -- Додаткові примітки
                     created_at TEXT NOT NULL               -- Дата та час створення запису
                 )''')

    # --- ТАБЛИЦЯ ОПЕРАЦІЙ ---
    # Журнал всіх операцій надходження (income) та відпуску (outcome) товарів
    c.execute('''CREATE TABLE IF NOT EXISTS operations
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Унікальний ID операції
        product_id INTEGER NOT NULL,           -- ID товару, з яким проводиться операція
        type TEXT NOT NULL,                    -- Тип операції: "income" (надходження) або "outcome" (відпуск)
        quantity INTEGER NOT NULL,             -- Кількість товару в операції
        date TEXT NOT NULL,                    -- Дата операції (формат: YYYY-MM-DD)
        time TEXT NOT NULL,                    -- Час операції (формат: HH:MM:SS)
        supplier_id INTEGER,                   -- ID постачальника (для операцій надходження)
        client_id INTEGER,                     -- ID клієнта (для операцій відпуску)
        invoice_number TEXT,                   -- Номер накладної/рахунку
        notes TEXT,                            -- Додаткові примітки
        FOREIGN KEY (product_id) REFERENCES products (id),      -- Зв'язок з товаром
        FOREIGN KEY (supplier_id) REFERENCES suppliers (id),    -- Зв'язок з постачальником
        FOREIGN KEY (client_id) REFERENCES clients (id)         -- Зв'язок з клієнтом
    )''')

    # --- ТАБЛИЦЯ ПЕРЕМІЩЕНЬ ТОВАРІВ ---
    # Історія переміщень товарів між різними локаціями на складі
    c.execute('''CREATE TABLE IF NOT EXISTS movements
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Унікальний ID переміщення
        product_id INTEGER NOT NULL,           -- ID товару, який переміщується
        from_warehouse TEXT NOT NULL,          -- З якого складу
        from_shelf TEXT NOT NULL,              -- З якого стелажу
        from_rack TEXT NOT NULL,               -- З якої полиці
        to_warehouse TEXT NOT NULL,            -- На який склад
        to_shelf TEXT NOT NULL,                -- На який стелаж
        to_rack TEXT NOT NULL,                 -- На яку полицю
        date TEXT NOT NULL,                    -- Дата переміщення
        time TEXT NOT NULL,                    -- Час переміщення
        FOREIGN KEY (product_id) REFERENCES products (id)  -- Зв'язок з товаром
    )''')

    print("Всі таблиці створено/перевірено")  # Повідомлення в консоль

    # Зберігаємо зміни та закриваємо з'єднання з БД
    conn.commit()
    conn.close()


# ============================================================================
# ФУНКЦІЯ ДОДАВАННЯ ТЕСТОВИХ ДАНИХ
# ============================================================================
def add_sample_data():
    """
    Автоматично додає тестові дані при створенні нової БД.
    Це допомагає одразу побачити, як працює система, без ручного введення.
    Включає: постачальників, клієнтів, товари, операції та переміщення.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Перевіряємо, чи вже є дані в таблиці products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] > 0:  # Якщо є хоча б один товар
        print("ℹ️  Дані вже існують, пропускаємо додавання зразкових даних")
        conn.close()
        return  # Виходимо з функції, щоб не дублювати дані

    print("Додавання тестових даних...")

    import random  # Для генерації випадкових значень
    from datetime import datetime, timedelta  # Для роботи з датами

    # === ДОДАВАННЯ ПОСТАЧАЛЬНИКІВ ===
    # Список кортежів з інформацією про 5 тестових постачальників
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

    supplier_ids = []  # Список для збереження ID створених постачальників
    for supplier in suppliers_data:
        # Вставляємо кожного постачальника в БД
        c.execute('''INSERT INTO suppliers
                         (name, contact_person, phone, email, address, notes, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (*supplier, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))  # *supplier розпаковує кортеж
        supplier_ids.append(c.lastrowid)  # Зберігаємо ID щойно створеного запису

    print(f"Додано {len(supplier_ids)} постачальників")

    # === ДОДАВАННЯ КЛІЄНТІВ ===
    # Список кортежів з інформацією про 5 тестових клієнтів
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

    client_ids = []  # Список для збереження ID створених клієнтів
    for client in clients_data:
        # Вставляємо кожного клієнта в БД
        c.execute('''INSERT INTO clients
                         (name, contact_person, phone, email, address, notes, created_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (*client, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        client_ids.append(c.lastrowid)

    print(f"Додано {len(client_ids)} клієнтів")

    # === ДОДАВАННЯ ТОВАРІВ ===
    # Список назв товарів для тестування
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

    # Визначаємо можливі локації на складі
    warehouses = ['1', '2', '3']  # 3 склади
    shelves = ['A', 'B', 'C', 'D']  # 4 стелажі на кожному складі
    racks = ['1', '2', '3', '4', '5']  # 5 полиць на кожному стелажі

    # Генеруємо всі можливі комбінації локацій
    locations = []
    for w in warehouses:
        for s in shelves:
            for r in racks[:3]:  # Беремо тільки перші 3 полиці для тестування
                locations.append((w, s, r))
                try:
                    # Додаємо локацію в таблицю locations
                    c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                              (w, s, r))
                except:
                    pass  # Ігноруємо помилку, якщо локація вже існує

    random.shuffle(locations)  # Перемішуємо локації для випадкового розподілу товарів

    product_ids = []  # Список для збереження ID створених товарів
    for i, name in enumerate(product_names, 1):  # enumerate починається з 1
        loc = locations[i - 1]  # Беремо наступну локацію зі списку
        number = f"ART-{1000 + i}"  # Генеруємо артикул (ART-1001, ART-1002, ...)
        quantity = random.randint(10, 100)  # Випадкова кількість від 10 до 100
        price = round(random.randint(100, 50000), 2)  # Випадкова ціна від 100 до 50000

        # Вставляємо товар в БД
        c.execute('''INSERT INTO products
                         (name, number, quantity, price, warehouse_number, shelf, rack)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (name, number, quantity, price, loc[0], loc[1], loc[2]))

        product_ids.append(c.lastrowid)  # Зберігаємо ID товару

    print(f"Додано {len(product_ids)} товарів")

    # === ДОДАВАННЯ ОПЕРАЦІЙ (НАДХОДЖЕННЯ ТА ВІДПУСКИ) ===
    for product_id in product_ids:
        # Генеруємо 3-4 операції надходження для кожного товару
        num_income = random.randint(3, 4)
        for _ in range(num_income):
            # Генеруємо дату в минулому (від 1 до 30 днів тому)
            days_ago = random.randint(1, 30)
            op_date = datetime.now() - timedelta(days=days_ago)
            date_str = op_date.strftime('%Y-%m-%d')
            time_str = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00"  # Час від 08:00 до 18:59

            qty = random.randint(10, 30)  # Кількість надходження
            supplier_id = random.choice(supplier_ids)  # Випадковий постачальник
            invoice_num = f"ПН-{random.randint(1000, 9999)}"  # Номер прибуткової накладної

            # Вставляємо операцію надходження
            c.execute('''INSERT INTO operations
                             (product_id, type, quantity, date, time, supplier_id, invoice_number)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (product_id, 'income', qty, date_str, time_str, supplier_id, invoice_num))

        # Генеруємо 2-3 операції відпуску для кожного товару
        num_outcome = random.randint(2, 3)
        for _ in range(num_outcome):
            # Генеруємо дату в минулому (від 0 до 25 днів тому)
            days_ago = random.randint(0, 25)
            op_date = datetime.now() - timedelta(days=days_ago)
            date_str = op_date.strftime('%Y-%m-%d')
            time_str = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00"

            qty = random.randint(5, 15)  # Кількість відпуску (менше ніж надходження)
            client_id = random.choice(client_ids)  # Випадковий клієнт
            invoice_num = f"ВН-{random.randint(1000, 9999)}"  # Номер видаткової накладної

            # Вставляємо операцію відпуску
            c.execute('''INSERT INTO operations
                             (product_id, type, quantity, date, time, client_id, invoice_number)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (product_id, 'outcome', qty, date_str, time_str, client_id, invoice_num))

    print("Додано операції з прив'язкою до постачальників/клієнтів")

    # === ДОДАВАННЯ ПЕРЕМІЩЕНЬ ===
    for i in range(3):  # Створюємо 3 тестові переміщення
        product_id = random.choice(product_ids)  # Випадковий товар

        # Отримуємо поточну локацію товару
        c.execute('''SELECT warehouse_number, shelf, rack
                     FROM products
                     WHERE id = ?''', (product_id,))
        from_loc = c.fetchone()

        # Вибираємо нову локацію (відмінну від поточної)
        to_loc = random.choice([l for l in locations[:10] if l != from_loc])

        # Генеруємо дату переміщення (від 0 до 15 днів тому)
        days_ago = random.randint(0, 15)
        move_date = datetime.now() - timedelta(days=days_ago)
        date_str = move_date.strftime('%Y-%m-%d')
        time_str = f"{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00"

        # Вставляємо запис про переміщення
        c.execute('''INSERT INTO movements
                     (product_id, from_warehouse, from_shelf, from_rack,
                      to_warehouse, to_shelf, to_rack, date, time)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, from_loc[0], from_loc[1], from_loc[2],
                   to_loc[0], to_loc[1], to_loc[2], date_str, time_str))

    print("Додано історію переміщень")

    # Зберігаємо всі зміни та закриваємо з'єднання
    conn.commit()
    conn.close()

    # Виводимо підсумкову інформацію
    print("\n✅ Тестові дані успішно додано!")
    print(f"""
📊 Підсумок:
   • Постачальників: {len(supplier_ids)}
   • Клієнтів: {len(client_ids)}
   • Товарів: {len(product_ids)}
   • Операцій: ~{len(product_ids) * 6}
   • Переміщень: 3
""")


# ============================================================================
# ДОПОМІЖНА ФУНКЦІЯ ДЛЯ ВИКОНАННЯ SQL-ЗАПИТІВ
# ============================================================================
def query_db(query, args=(), one=False):
    """
    Універсальна функція для виконання SQL-запитів.
    
    Параметри:
    - query: SQL-запит (рядок)
    - args: параметри для запиту (кортеж)
    - one: якщо True, повертає тільки перший результат, інакше всі результати
    
    Повертає: результат запиту або None
    """
    conn = sqlite3.connect(DB_NAME)  # Підключаємося до БД
    c = conn.cursor()  # Створюємо курсор
    c.execute(query, args)  # Виконуємо запит з параметрами
    result = c.fetchall()  # Отримуємо всі результати
    conn.commit()  # Зберігаємо зміни (якщо це був INSERT/UPDATE/DELETE)
    conn.close()  # Закриваємо з'єднання
    return (result[0] if result else None) if one else result  # Повертаємо результат


# ============================================================================
# ДЕКОРАТОР ДЛЯ ПЕРЕВІРКИ АВТОРИЗАЦІЇ
# ============================================================================
def login_required(f):
    """
    Декоратор, який перевіряє, чи користувач увійшов в систему.
    Якщо ні - перенаправляє на сторінку входу.
    Використовується для захисту всіх основних роутів додатку.
    """
    def wrapper(*args, **kwargs):
        # Перевіряємо, чи є ключ 'logged_in' в сесії користувача
        if 'logged_in' not in session:
            # Якщо користувач не авторизований, перенаправляємо на сторінку входу
            return redirect(url_for('login_page'))
        # Якщо авторизований, виконуємо оригінальну функцію
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__  # Зберігаємо ім'я оригінальної функції
    return wrapper


# ============================================================================
# РОУТИ ДЛЯ АВТОРИЗАЦІЇ
# ============================================================================

@app.route('/login')
def login_page():
    """
    Відображає сторінку входу в систему.
    Якщо користувач вже авторизований, перенаправляє на головну сторінку.
    """
    if 'logged_in' in session:  # Перевіряємо, чи вже авторизований
        return redirect(url_for('index'))  # Перенаправляємо на головну
    return render_template('login.html')  # Показуємо форму входу


@app.route('/login', methods=['POST'])
def login():
    """
    API для обробки входу в систему.
    Приймає JSON з логіном та паролем, перевіряє їх та створює сесію.
    """
    data = request.get_json()  # Отримуємо дані з запиту у форматі JSON
    username = data.get('username')  # Витягуємо логін
    password = data.get('password')  # Витягуємо пароль
    
    # Перевіряємо, чи збігаються логін та пароль з константами
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['logged_in'] = True  # Встановлюємо прапорець авторизації
        session['username'] = username  # Зберігаємо ім'я користувача в сесії
        return jsonify({"success": True})  # Повертаємо успіх
    else:
        # Якщо дані невірні, повертаємо помилку з кодом 401 (Unauthorized)
        return jsonify({"error": "Невірний логін або пароль"}), 401


@app.route('/logout', methods=['POST'])
def logout():
    """
    API для виходу з системи.
    Очищає сесію користувача.
    """
    session.clear()  # Видаляємо всі дані з сесії
    return jsonify({"success": True})  # Підтверджуємо вихід


# ============================================================================
# РОУТИ ДЛЯ ОСНОВНИХ СТОРІНОК
# ============================================================================

@app.route('/')
@login_required  # Доступ тільки для авторизованих користувачів
def index():
    """
    Головна сторінка додатку.
    Відображає загальний інтерфейс управління складом.
    """
    return render_template('index.html')


@app.route('/stock')
@login_required  # Доступ тільки для авторизованих користувачів
def stock_page():
    """
    Сторінка складського обліку.
    Відображає список всіх товарів на складі.
    """
    return render_template('stock.html')


@app.route('/operations')
@login_required  # Доступ тільки для авторизованих користувачів
def operations_page():
    """
    Сторінка операцій.
    Відображає журнал надходжень та відпусків товарів.
    """
    return render_template('operations.html')


# ============================================================================
# API ДЛЯ РОБОТИ З ТОВАРАМИ
# ============================================================================

@app.route('/products', methods=['GET'])
@login_required  # Доступ тільки для авторизованих користувачів
def get_products():
    """
    API для отримання списку всіх товарів.
    Повертає JSON-масив з інформацією про кожен товар.
    """
    # Виконуємо SQL-запит для отримання всіх товарів
    products = query_db('''SELECT id, name, number, quantity, price,
                                  warehouse_number, shelf, rack
                           FROM products''')
    
    # Перетворюємо результат в список словників (JSON-сумісний формат)
    result = [
        {
            "id": row[0],               # ID товару
            "name": row[1],             # Назва товару
            "number": row[2],           # Артикул
            "quantity": row[3],         # Кількість
            "price": row[4],            # Ціна
            "warehouse_number": row[5], # Номер складу
            "shelf": row[6],            # Стелаж
            "rack": row[7],             # Полиця
        }
        for row in products
    ]
    return jsonify(result)  # Повертаємо JSON


@app.route('/products', methods=['POST'])
@login_required  # Доступ тільки для авторизованих користувачів
def add_product():
    """
    API для додавання нового товару.
    Приймає JSON з даними товару, перевіряє їх та додає в БД.
    """
    data = request.get_json()  # Отримуємо JSON-дані з запиту
    
    # Витягуємо дані з запиту
    name = data.get('name')
    number = data.get('number')
    quantity = data.get('quantity', 0)  # За замовчуванням 0
    price = data.get('price')
    warehouse_number = data.get('warehouse_number')
    shelf = data.get('shelf')
    rack = data.get('rack')

    # Перевіряємо, чи вказана назва товару (обов'язкове поле)
    if not name:
        return jsonify({"error": "Назва товару обов'язкова"}), 400  # Код 400 = Bad Request

    conn = sqlite3.connect(DB_NAME)  # Підключаємося до БД
    c = conn.cursor()

    # Спочатку додаємо локацію, якщо її ще немає
    try:
        c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                  (warehouse_number, shelf, rack))
    except sqlite3.IntegrityError:
        # Якщо локація вже існує, ігноруємо помилку
        pass

    # Перевіряємо, чи вже є товар на цій локації (на одному місці може бути тільки один товар)
    c.execute('''SELECT id FROM products 
                 WHERE warehouse_number=? AND shelf=? AND rack=?''',
              (warehouse_number, shelf, rack))
    existing = c.fetchone()

    if existing:
        # Якщо локація зайнята, повертаємо помилку
        conn.close()
        return jsonify({"error": "Товар у цьому місці вже існує"}), 400

    # Додаємо новий товар в БД
    c.execute('''INSERT INTO products (name, number, quantity, price, warehouse_number, shelf, rack)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (name, number, quantity, price, warehouse_number, shelf, rack))

    conn.commit()  # Зберігаємо зміни
    conn.close()  # Закриваємо з'єднання
    return jsonify({"success": True})  # Підтверджуємо успіх


@app.route('/products/<int:product_id>', methods=['PUT'])
@login_required  # Доступ тільки для авторизованих користувачів
def update_product(product_id):
    """
    API для оновлення даних товару.
    Параметр product_id передається в URL (наприклад: /products/5).
    """
    data = request.get_json()  # Отримуємо нові дані товару з запиту
    
    # Витягуємо дані
    name = data.get('name')
    number = data.get('number')
    quantity = data.get('quantity')
    price = data.get('price')
    
    # Оновлюємо товар в БД
    query_db("UPDATE products SET name=?, number=?, quantity=?, price=? WHERE id=?",
             (name, number, quantity, price, product_id))
    
    return jsonify({"success": True})  # Підтверджуємо успіх


@app.route('/products/<int:product_id>', methods=['DELETE'])
@login_required  # Доступ тільки для авторизованих користувачів
def delete_product(product_id):
    """
    API для видалення товару.
    Видаляє товар з БД за його ID.
    """
    query_db("DELETE FROM products WHERE id=?", (product_id,))  # Видаляємо товар
    return jsonify({"success": True})  # Підтверджуємо успіх


# ============================================================================
# РОУТИ ДЛЯ РОБОТИ З ПОСТАЧАЛЬНИКАМИ
# ============================================================================

@app.route('/suppliers')
@login_required  # Доступ тільки для авторизованих користувачів
def suppliers_page():
    """
    Сторінка постачальників.
    Відображає список всіх постачальників.
    """
    return render_template('suppliers.html')


@app.route('/api/suppliers', methods=['GET'])
@login_required  # Доступ тільки для авторизованих користувачів
def get_suppliers():
    """
    API для отримання списку всіх постачальників.
    Повертає JSON-масив з інформацією про кожного постачальника.
    """
    try:
        # Отримуємо всіх постачальників, відсортованих за назвою
        suppliers = query_db('''SELECT id, name, contact_person, phone, email, address, notes, created_at
                                FROM suppliers
                                ORDER BY name''')
        
        # Перетворюємо в JSON-сумісний формат
        result = [
            {
                "id": row[0],             # ID постачальника
                "name": row[1],           # Назва компанії
                "contact_person": row[2], # Контактна особа
                "phone": row[3],          # Телефон
                "email": row[4],          # Email
                "address": row[5],        # Адреса
                "notes": row[6],          # Примітки
                "created_at": row[7]      # Дата створення
            }
            for row in suppliers
        ]
        return jsonify(result)  # Повертаємо JSON
    except Exception as e:
        # Якщо сталася помилка, виводимо її в консоль та повертаємо порожній масив
        print(f"Помилка get_suppliers: {e}")
        return jsonify([])


@app.route('/api/suppliers', methods=['POST'])
@login_required  # Доступ тільки для авторизованих користувачів
def add_supplier():
    """
    API для додавання нового постачальника.
    Приймає JSON з даними постачальника, перевіряє їх та додає в БД.
    """
    try:
        data = request.get_json()  # Отримуємо дані з запиту
        
        # Витягуємо та очищаємо (видаляємо зайві пробіли) дані
        name = data.get('name', '').strip()
        contact_person = data.get('contact_person', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        notes = data.get('notes', '').strip()

        # Перевіряємо, чи вказана назва (обов'язкове поле)
        if not name:
            return jsonify({"error": "Назва постачальника обов'язкова"}), 400

        # Генеруємо поточну дату та час
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Додаємо постачальника в БД
        query_db('''INSERT INTO suppliers
                        (name, contact_person, phone, email, address, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (name, contact_person, phone, email, address, notes, created_at))

        return jsonify({"success": True})  # Підтверджуємо успіх
    except Exception as e:
        # При помилці виводимо її в консоль та повертаємо повідомлення про помилку
        print(f"Помилка add_supplier: {e}")
        return jsonify({"error": str(e)}), 500  # Код 500 = Internal Server Error


@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
@login_required  # Доступ тільки для авторизованих користувачів
def update_supplier(supplier_id):
    """
    API для оновлення даних постачальника.
    Параметр supplier_id передається в URL.
    """
    try:
        data = request.get_json()  # Отримуємо нові дані з запиту
        
        # Витягуємо та очищаємо дані
        name = data.get('name', '').strip()
        contact_person = data.get('contact_person', '').strip()
        phone = data.get('phone', '').strip()
        email = data.get('email', '').strip()
        address = data.get('address', '').strip()
        notes = data.get('notes', '').strip()

        # Перевіряємо, чи вказана назва (обов'язкове поле)
        if not name:
            return jsonify({"error": "Назва постачальника обов'язкова"}), 400

        # Оновлюємо дані постачальника в БД
        query_db('''UPDATE suppliers
                    SET name=?, contact_person=?, phone=?, email=?, address=?, notes=?
                    WHERE id = ?''',
                 (name, contact_person, phone, email, address, notes, supplier_id))

        return jsonify({"success": True})  # Підтверджуємо успіх
    except Exception as e:
        print(f"Помилка update_supplier: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
@login_required  # Доступ тільки для авторизованих користувачів
def delete_supplier(supplier_id):
    """
    API для видалення постачальника.
    Перед видаленням перевіряє, чи немає операцій з цим постачальником.
    """
    try:
        # Перевіряємо, чи є операції з цим постачальником
        ops = query_db("SELECT COUNT(*) FROM operations WHERE supplier_id=?", (supplier_id,), one=True)
        if ops and ops[0] > 0:
            # Якщо є операції, заборонясмо видалення
            return jsonify({"error": f"Неможливо видалити! Є {ops[0]} операцій з цим постачальником"}), 400

        # Якщо операцій немає, видаляємо постачальника
        query_db("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        return jsonify({"success": True})  # Підтверджуємо успіх
    except Exception as e:
        print(f"Помилка delete_supplier: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers/<int:supplier_id>/operations', methods=['GET'])
@login_required  # Доступ тільки для авторизованих користувачів
def get_supplier_operations(supplier_id):
    """
    API для отримання всіх операцій надходження від конкретного постачальника.
    Використовується для перегляду історії закупівель у постачальника.
    """
    try:
        # Отримуємо всі операції надходження від цього постачальника
        ops = query_db('''SELECT o.id, o.date, o.time, o.quantity, o.invoice_number, p.name, p.number
                          FROM operations o
                          JOIN products p ON o.product_id = p.id
                          WHERE o.supplier_id = ? AND o.type = 'income'
                          ORDER BY o.date DESC, o.time DESC''',
                       (supplier_id,))
        
        # Перетворюємо в JSON-формат
        result = [
            {
                "id": row[0],             # ID операції
                "date": row[1],           # Дата операції
                "time": row[2],           # Час операції
                "quantity": row[3],       # Кількість товару
                "invoice_number": row[4], # Номер накладної
                "product_name": row[5],   # Назва товару
                "product_number": row[6]  # Артикул товару
            }
            for row in ops
        ]
        return jsonify(result)  # Повертаємо JSON
    except Exception as e:
        print(f"Помилка get_supplier_operations: {e}")
        return jsonify([])


# ============================================================================
# РОУТИ ДЛЯ РОБОТИ З КЛІЄНТАМИ
# ============================================================================
# (Структура аналогічна до постачальників, тому коментарі скорочені)

@app.route('/clients')
@login_required
def clients_page():
    """Сторінка клієнтів"""
    return render_template('clients.html')


@app.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    """API для отримання списку всіх клієнтів"""
    try:
        clients = query_db('''SELECT id, name, contact_person, phone, email, address, notes, created_at
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
    """API для додавання нового клієнта"""
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
    """API для оновлення даних клієнта"""
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
                    SET name=?, contact_person=?, phone=?, email=?, address=?, notes=?
                    WHERE id = ?''',
                 (name, contact_person, phone, email, address, notes, client_id))

        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка update_client: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
@login_required
def delete_client(client_id):
    """
    API для видалення клієнта.
    Перед видаленням перевіряє, чи немає операцій з цим клієнтом.
    """
    try:
        # Перевіряємо наявність операцій
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
    """
    API для отримання всіх операцій відпуску конкретному клієнту.
    Використовується для перегляду історії продажів клієнту.
    """
    try:
        ops = query_db('''SELECT o.id, o.date, o.time, o.quantity, o.invoice_number, p.name, p.number
                          FROM operations o
                          JOIN products p ON o.product_id = p.id
                          WHERE o.client_id = ? AND o.type = 'outcome'
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


# ============================================================================
# API ДЛЯ РОБОТИ З ОПЕРАЦІЯМИ
# ============================================================================

@app.route('/api/operations', methods=['GET'])
@login_required
def get_operations():
    """
    API для отримання останніх 20 операцій (надходження та відпуски).
    Включає інформацію про товар, постачальника/клієнта та накладну.
    """
    try:
        # Отримуємо останні 20 операцій з JOIN-ами до товарів, постачальників та клієнтів
        ops = query_db('''SELECT o.id, o.type, o.quantity, o.date, o.time, 
                                 p.name, p.number, o.invoice_number,
                                 s.name as supplier_name, c.name as client_name
                          FROM operations o
                          JOIN products p ON o.product_id = p.id
                          LEFT JOIN suppliers s ON o.supplier_id = s.id  -- LEFT JOIN, бо може не бути постачальника
                          LEFT JOIN clients c ON o.client_id = c.id      -- LEFT JOIN, бо може не бути клієнта
                          ORDER BY o.date DESC, o.time DESC
                          LIMIT 20''')  # Обмежуємо до 20 записів для швидкості
        
        result = [
            {
                "id": row[0],             # ID операції
                "type": row[1],           # Тип: "income" або "outcome"
                "quantity": row[2],       # Кількість
                "date": row[3],           # Дата
                "time": row[4],           # Час
                "product_name": row[5],   # Назва товару
                "product_number": row[6], # Артикул товару
                "invoice_number": row[7], # Номер накладної
                "supplier_name": row[8],  # Назва постачальника (може бути None)
                "client_name": row[9]     # Назва клієнта (може бути None)
            }
            for row in ops
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_operations: {e}")
        return jsonify([])


@app.route('/operations/outcome', methods=['POST'])
@login_required
def add_outcome():
    """
    API для додавання операції відпуску товару клієнту.
    Перевіряє наявність товару, зменшує кількість та записує операцію.
    """
    try:
        data = request.get_json()  # Отримуємо дані з запиту
        
        # Витягуємо дані
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        date_input = data.get('date')
        client_id = data.get('client_id')
        invoice_number = data.get('invoice_number', '').strip()

        # Валідація даних
        if not product_id or not quantity or quantity <= 0:
            return jsonify({"error": "Невірні дані"}), 400

        if not client_id:
            return jsonify({"error": "Виберіть клієнта"}), 400

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # Перевіряємо наявність товару на складі
        c.execute("SELECT quantity FROM products WHERE id = ?", (product_id,))
        result = c.fetchone()

        if not result:
            conn.close()
            return jsonify({"error": "Товар не знайдено"}), 404

        # Перевіряємо, чи вистачає товару для відпуску
        if result[0] < quantity:
            conn.close()
            return jsonify({"error": f"Недостатньо товару на складі. Доступно: {result[0]}"}), 400

        # Перевіряємо існування клієнта
        c.execute("SELECT id FROM clients WHERE id = ?", (client_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({"error": "Клієнт не знайдено"}), 404

        # Зменшуємо кількість товару на складі
        c.execute("UPDATE products SET quantity = quantity - ? WHERE id = ?", (quantity, product_id))

        # Записуємо операцію відпуску
        now = datetime.now()
        date_str = date_input if date_input else now.strftime('%Y-%m-%d')  # Якщо дата не вказана, беремо поточну
        time_str = now.strftime('%H:%M:%S')  # Час завжди поточний

        c.execute('''INSERT INTO operations
                         (product_id, type, quantity, date, time, client_id, invoice_number)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, 'outcome', quantity, date_str, time_str, client_id, invoice_number))

        conn.commit()  # Зберігаємо зміни
        conn.close()  # Закриваємо з'єднання

        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка add_outcome: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================================
# РОУТИ ДЛЯ РОБОТИ З РУХОМ ТОВАРІВ
# ============================================================================

@app.route('/movement')
@login_required
def movement_page():
    """Сторінка перегляду руху товарів (історія операцій)"""
    return render_template('movement.html')


@app.route('/api/operations/all', methods=['GET'])
@login_required
def get_all_operations():
    """
    API для отримання ВСІХ операцій (без обмеження).
    Використовується на сторінці руху товарів.
    """
    try:
        # Отримуємо всі операції (без LIMIT)
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


# ============================================================================
# РОУТИ ДЛЯ ПЕРЕМІЩЕННЯ ТОВАРІВ МІЖ ЛОКАЦІЯМИ
# ============================================================================

@app.route('/relocation')
@login_required
def relocation_page():
    """Сторінка переміщення товарів між локаціями на складі"""
    return render_template('relocation.html')


@app.route('/relocation/move', methods=['POST'])
@login_required
def move_product():
    """
    API для переміщення товару з однієї локації на іншу.
    Перевіряє, чи нова локація вільна, оновлює товар та записує історію.
    """
    try:
        data = request.get_json()
        print(f"Отримано дані: {data}")  # Лог для відладки
        
        # Витягуємо дані
        product_id = data.get('product_id')
        to_warehouse = data.get('to_warehouse')
        to_shelf = data.get('to_shelf')
        to_rack = data.get('to_rack')
        
        print(f"product_id={product_id}, to_warehouse={to_warehouse}, to_shelf={to_shelf}, to_rack={to_rack}")
        
        # Перевіряємо, чи всі поля заповнені
        if not all([product_id, to_warehouse, to_shelf, to_rack]):
            print("Помилка: Не всі поля заповнені!")
            return jsonify({"error": "Заповніть всі поля!"}), 400
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Отримуємо поточну локацію товару та його назву
        c.execute('''SELECT warehouse_number, shelf, rack, name 
                     FROM products WHERE id = ?''', (product_id,))
        current = c.fetchone()
        
        if not current:
            conn.close()
            return jsonify({"error": "Товар не знайдено"}), 404
        
        from_warehouse, from_shelf, from_rack, product_name = current
        
        # Перевіряємо, чи не переміщуємо товар у ту саму локацію
        if (from_warehouse == to_warehouse and 
            from_shelf == to_shelf and 
            from_rack == to_rack):
            conn.close()
            return jsonify({"error": "Товар вже знаходиться в цій локації!"}), 400
        
        # Перевіряємо, чи вільна нова локація
        c.execute('''SELECT id FROM products 
                     WHERE warehouse_number=? AND shelf=? AND rack=?''',
                  (to_warehouse, to_shelf, to_rack))
        existing = c.fetchone()
        
        if existing:
            conn.close()
            return jsonify({"error": "Нова локація вже зайнята іншим товаром!"}), 400
        
        # Додаємо нову локацію в таблицю locations, якщо її ще немає
        try:
            c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                      (to_warehouse, to_shelf, to_rack))
        except sqlite3.IntegrityError:
            pass  # Локація вже існує, ігноруємо помилку
        
        # Оновлюємо локацію товару в таблиці products
        c.execute('''UPDATE products 
                     SET warehouse_number=?, shelf=?, rack=? 
                     WHERE id=?''',
                  (to_warehouse, to_shelf, to_rack, product_id))
        
        # Записуємо переміщення в історію (таблиця movements)
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        c.execute('''INSERT INTO movements 
                     (product_id, from_warehouse, from_shelf, from_rack, 
                      to_warehouse, to_shelf, to_rack, date, time)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, from_warehouse, from_shelf, from_rack,
                   to_warehouse, to_shelf, to_rack, date_str, time_str))
        
        conn.commit()  # Зберігаємо зміни
        conn.close()  # Закриваємо з'єднання
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Помилка move_product: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/relocation/history', methods=['GET'])
@login_required
def get_movement_history():
    """
    API для отримання історії переміщень товарів.
    Повертає останні 50 переміщень.
    """
    try:
        # Отримуємо історію переміщень з інформацією про товар
        movements = query_db('''SELECT m.id, m.date, m.time, 
                                       p.name, p.number,
                                       m.from_warehouse, m.from_shelf, m.from_rack,
                                       m.to_warehouse, m.to_shelf, m.to_rack
                                FROM movements m
                                JOIN products p ON m.product_id = p.id
                                ORDER BY m.date DESC, m.time DESC
                                LIMIT 50''')  # Останні 50 переміщень
        
        result = [
            {
                "id": row[0],             # ID переміщення
                "date": row[1],           # Дата
                "time": row[2],           # Час
                "product_name": row[3],   # Назва товару
                "product_number": row[4], # Артикул товару
                "from_warehouse": row[5], # З якого складу
                "from_shelf": row[6],     # З якого стелажу
                "from_rack": row[7],      # З якої полиці
                "to_warehouse": row[8],   # На який склад
                "to_shelf": row[9],       # На який стелаж
                "to_rack": row[10]        # На яку полицю
            }
            for row in movements
        ]
        return jsonify(result)
    except Exception as e:
        print(f"Помилка get_movement_history: {e}")
        return jsonify([])


# ============================================================================
# РОУТИ ДЛЯ ДАШБОРДУ (ПАНЕЛІ КЕРУВАННЯ)
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard_page():
    """Головна панель керування з аналітикою та статистикою"""
    return render_template('dashboard.html')


@app.route('/api/operations/today', methods=['GET'])
@login_required
def get_today_operations():
    """
    API для отримання операцій за сьогоднішній день.
    Використовується на дашборді для відображення активності за день.
    """
    try:
        today = datetime.now().strftime('%Y-%m-%d')  # Поточна дата у форматі YYYY-MM-DD
        
        # Отримуємо тільки операції за сьогодні
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


# ============================================================================
# API ДЛЯ НАДХОДЖЕННЯ ТОВАРУ (РОЗШИРЕНИЙ ФУНКЦІОНАЛ)
# ============================================================================

@app.route('/operations/income', methods=['POST'])
@login_required
def add_income():
    """
    API для додавання операції надходження товару.
    
    Підтримує ДВА РЕЖИМИ:
    1. Надходження існуючого товару (збільшення кількості)
    2. Надходження нового товару (створення товару + додавання кількості)
    
    Режим визначається параметром is_new_product у JSON.
    """
    try:
        data = request.get_json()
        
        # Витягуємо загальні дані
        quantity = data.get('quantity')
        date_input = data.get('date')
        supplier_id = data.get('supplier_id')
        invoice_number = data.get('invoice_number', '').strip()
        is_new_product = data.get('is_new_product', False)  # Чи це новий товар?

        # Валідація загальних даних
        if not quantity or quantity <= 0:
            return jsonify({"error": "Невірна кількість"}), 400

        if not supplier_id:
            return jsonify({"error": "Виберіть постачальника"}), 400

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        # Перевіряємо існування постачальника
        c.execute("SELECT id FROM suppliers WHERE id = ?", (supplier_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({"error": "Постачальник не знайдено"}), 404

        product_id = None  # ID товару (буде визначено нижче)

        # === РЕЖИМ 1: СТВОРЕННЯ НОВОГО ТОВАРУ ===
        if is_new_product:
            # Витягуємо дані для нового товару
            product_name = data.get('product_name', '').strip()
            product_number = data.get('product_number', '').strip()
            product_price = data.get('product_price', 0)
            warehouse_number = data.get('warehouse_number', '').strip()
            shelf = data.get('shelf', '').strip()
            rack = data.get('rack', '').strip()

            # Перевіряємо обов'язкові поля
            if not product_name or not warehouse_number or not shelf or not rack:
                conn.close()
                return jsonify({"error": "Заповніть всі обов'язкові поля для нового товару"}), 400

            # Додаємо локацію в таблицю locations, якщо її немає
            try:
                c.execute("INSERT INTO locations (warehouse_number, shelf, rack) VALUES (?, ?, ?)",
                          (warehouse_number, shelf, rack))
            except sqlite3.IntegrityError:
                pass  # Локація вже існує

            # Перевіряємо, чи вільна ця локація
            c.execute('''SELECT id FROM products
                         WHERE warehouse_number = ? AND shelf = ? AND rack = ?''',
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

            product_id = c.lastrowid  # Отримуємо ID щойно створеного товару
            print(f"✅ Створено новий товар ID={product_id}")

        # === РЕЖИМ 2: НАДХОДЖЕННЯ ІСНУЮЧОГО ТОВАРУ ===
        else:
            product_id = data.get('product_id')

            if not product_id:
                conn.close()
                return jsonify({"error": "Виберіть товар"}), 400

            # Перевіряємо існування товару
            c.execute("SELECT id FROM products WHERE id = ?", (product_id,))
            if not c.fetchone():
                conn.close()
                return jsonify({"error": "Товар не знайдено"}), 404

            # Збільшуємо кількість існуючого товару
            c.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?",
                      (quantity, product_id))

        # === ЗАПИС ОПЕРАЦІЇ НАДХОДЖЕННЯ (ДЛЯ ОБОХ РЕЖИМІВ) ===
        now = datetime.now()
        date_str = date_input if date_input else now.strftime('%Y-%m-%d')  # Дата з запиту або поточна
        time_str = now.strftime('%H:%M:%S')  # Час завжди поточний

        # Додаємо операцію в таблицю operations
        c.execute('''INSERT INTO operations
                         (product_id, type, quantity, date, time, supplier_id, invoice_number)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (product_id, 'income', quantity, date_str, time_str, supplier_id, invoice_number))

        conn.commit()  # Зберігаємо всі зміни
        conn.close()  # Закриваємо з'єднання

        return jsonify({"success": True})

    except Exception as e:
        # При будь-якій помилці виводимо детальну інформацію
        print(f"Помилка add_income: {e}")
        import traceback
        traceback.print_exc()  # Виводимо повний traceback для відладки
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ТОЧКА ВХОДУ В ПРОГРАМУ
# ============================================================================

if __name__ == '__main__':
    # Перевіряємо, чи існує файл бази даних
    db_exists = os.path.exists(DB_NAME)

    if not db_exists:
        # Якщо БД не існує, створюємо її
        print("⚠️  База даних не знайдена, створюємо нову...")
        init_db()  # Створюємо структуру таблиць
        print("✅ База даних створена!")

        # Автоматично додаємо тестові дані для демонстрації
        add_sample_data()
    else:
        # Якщо БД існує, просто перевіряємо/оновлюємо структуру таблиць
        print("ℹ️  База даних знайдена, перевіряємо структуру...")
        init_db()

    # Виводимо інформацію про запуск
    print("\n" + "="*60)
    print("🚀 Flask-сервер успішно запущено!")
    print("="*60)
    print("📍 Адреса: http://127.0.0.1:5000")
    print("👤 Логін: адмін")
    print("🔑 Пароль: адмін")
    print("="*60 + "\n")
    
    # Запускаємо Flask-сервер
    # host='0.0.0.0' - доступ з будь-якого IP (не тільки localhost)
    # port=5000 - порт сервера
    # debug=True - режим розробки з автоперезавантаженням при змінах коду
    app.run(host='0.0.0.0', port=5000, debug=True)