import pytest
import sqlite3
import os
import sys
import json
from datetime import datetime

# Додаємо батьківську директорію до шляху
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, init_db, ADMIN_USERNAME, ADMIN_PASSWORD

# Глобальна змінна для тестової БД
TEST_DB_NAME = 'test_warehouse.db'


@pytest.fixture
def client():
    """Створює тестовий клієнт Flask"""
    # Використовуємо тестову базу даних
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'

    # Видаляємо стару тестову БД якщо існує
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)

    # Патчимо DB_NAME в модулі app
    import app as app_module
    original_db = app_module.DB_NAME
    app_module.DB_NAME = TEST_DB_NAME

    # Ініціалізуємо тестову БД
    init_db()

    with app.test_client() as client:
        with app.app_context():
            yield client

    # Відновлюємо оригінальну БД та очищуємо
    app_module.DB_NAME = original_db
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)


@pytest.fixture
def auth_client(client):
    """Автентифікований клієнт"""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = ADMIN_USERNAME
    return client


# ============ ТЕСТИ АВТОРИЗАЦІЇ ============

def test_login_page_accessible(client):
    """Перевірка доступності сторінки логіну"""
    response = client.get('/login')
    assert response.status_code == 200


def test_successful_login(client):
    """Успішний вхід з правильними даними"""
    response = client.post('/login',
                           data=json.dumps({
                               'username': ADMIN_USERNAME,
                               'password': ADMIN_PASSWORD
                           }),
                           content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True


def test_failed_login_wrong_password(client):
    """Невдалий вхід з неправильним паролем"""
    response = client.post('/login',
                           data=json.dumps({
                               'username': ADMIN_USERNAME,
                               'password': 'wrong_password'
                           }),
                           content_type='application/json')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data


def test_failed_login_wrong_username(client):
    """Невдалий вхід з неправильним логіном"""
    response = client.post('/login',
                           data=json.dumps({
                               'username': 'wrong_user',
                               'password': ADMIN_PASSWORD
                           }),
                           content_type='application/json')
    assert response.status_code == 401


def test_logout(auth_client):
    """Перевірка виходу з системи"""
    response = auth_client.post('/logout')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True


def test_protected_route_without_auth(client):
    """Доступ до захищеного роуту без авторизації"""
    response = client.get('/products')
    assert response.status_code == 302  # Редирект на логін


# ============ ТЕСТИ ТОВАРІВ ============

def test_get_empty_products_list(auth_client):
    """Отримання порожнього списку товарів"""
    response = auth_client.get('/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 0


def test_add_product_success(auth_client):
    """Успішне додавання товару"""
    product_data = {
        'name': 'Тестовий товар',
        'number': 'TEST-001',
        'quantity': 10,
        'price': 100.50,
        'warehouse_number': '1',
        'shelf': 'A',
        'rack': '1'
    }
    response = auth_client.post('/products',
                                data=json.dumps(product_data),
                                content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True


def test_add_product_without_name(auth_client):
    """Додавання товару без назви (помилка)"""
    product_data = {
        'number': 'TEST-002',
        'quantity': 5,
        'warehouse_number': '1',
        'shelf': 'B',
        'rack': '2'
    }
    response = auth_client.post('/products',
                                data=json.dumps(product_data),
                                content_type='application/json')
    assert response.status_code == 400


def test_add_duplicate_location_product(auth_client):
    """Додавання товару на зайняту локацію"""
    product_data = {
        'name': 'Товар 1',
        'warehouse_number': '1',
        'shelf': 'A',
        'rack': '1'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    # Спроба додати ще один товар на ту саму локацію
    response = auth_client.post('/products',
                                data=json.dumps(product_data),
                                content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_get_products_list(auth_client):
    """Отримання списку товарів"""
    # Додаємо товар
    product_data = {
        'name': 'Товар для списку',
        'number': 'LIST-001',
        'warehouse_number': '1',
        'shelf': 'C',
        'rack': '3'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    # Отримуємо список
    response = auth_client.get('/products')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1
    assert data[0]['name'] == 'Товар для списку'


def test_update_product(auth_client):
    """Оновлення товару"""
    # Додаємо товар
    product_data = {
        'name': 'Старий товар',
        'number': 'OLD-001',
        'quantity': 5,
        'price': 50.0,
        'warehouse_number': '2',
        'shelf': 'A',
        'rack': '1'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    # Оновлюємо товар
    update_data = {
        'name': 'Новий товар',
        'number': 'NEW-001',
        'quantity': 15,
        'price': 75.0
    }
    response = auth_client.put('/products/1',
                               data=json.dumps(update_data),
                               content_type='application/json')
    assert response.status_code == 200

    # Перевіряємо оновлення
    products = auth_client.get('/products')
    data = json.loads(products.data)
    assert data[0]['name'] == 'Новий товар'
    assert data[0]['quantity'] == 15


def test_delete_product(auth_client):
    """Видалення товару"""
    # Додаємо товар
    product_data = {
        'name': 'Товар для видалення',
        'warehouse_number': '3',
        'shelf': 'B',
        'rack': '2'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    # Видаляємо
    response = auth_client.delete('/products/1')
    assert response.status_code == 200

    # Перевіряємо що товар видалено
    products = auth_client.get('/products')
    data = json.loads(products.data)
    assert len(data) == 0


# ============ ТЕСТИ ПОСТАЧАЛЬНИКІВ ============

def test_get_empty_suppliers(auth_client):
    """Отримання порожнього списку постачальників"""
    response = auth_client.get('/api/suppliers')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 0


def test_add_supplier_success(auth_client):
    """Успішне додавання постачальника"""
    supplier_data = {
        'name': 'Тестовий постачальник',
        'contact_person': 'Іван Іванов',
        'phone': '+380501234567',
        'email': 'test@example.com',
        'address': 'Київ, вул. Тестова 1',
        'notes': 'Тестові нотатки'
    }
    response = auth_client.post('/api/suppliers',
                                data=json.dumps(supplier_data),
                                content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] == True


def test_add_supplier_without_name(auth_client):
    """Додавання постачальника без назви"""
    supplier_data = {
        'contact_person': 'Петро Петров',
        'phone': '+380501234567'
    }
    response = auth_client.post('/api/suppliers',
                                data=json.dumps(supplier_data),
                                content_type='application/json')
    assert response.status_code == 400


def test_update_supplier(auth_client):
    """Оновлення постачальника"""
    # Додаємо
    supplier_data = {'name': 'Старий постачальник'}
    auth_client.post('/api/suppliers',
                     data=json.dumps(supplier_data),
                     content_type='application/json')

    # Оновлюємо
    update_data = {
        'name': 'Новий постачальник',
        'phone': '+380671111111'
    }
    response = auth_client.put('/api/suppliers/1',
                               data=json.dumps(update_data),
                               content_type='application/json')
    assert response.status_code == 200


def test_delete_supplier_without_operations(auth_client):
    """Видалення постачальника без операцій"""
    supplier_data = {'name': 'Постачальник для видалення'}
    auth_client.post('/api/suppliers',
                     data=json.dumps(supplier_data),
                     content_type='application/json')

    response = auth_client.delete('/api/suppliers/1')
    assert response.status_code == 200


# ============ ТЕСТИ КЛІЄНТІВ ============

def test_add_client_success(auth_client):
    """Успішне додавання клієнта"""
    client_data = {
        'name': 'Тестовий клієнт',
        'contact_person': 'Марія Мар\'єнко',
        'phone': '+380991234567',
        'email': 'client@example.com'
    }
    response = auth_client.post('/api/clients',
                                data=json.dumps(client_data),
                                content_type='application/json')
    assert response.status_code == 200


def test_get_clients_list(auth_client):
    """Отримання списку клієнтів"""
    client_data = {'name': 'Клієнт 1'}
    auth_client.post('/api/clients',
                     data=json.dumps(client_data),
                     content_type='application/json')

    response = auth_client.get('/api/clients')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 1


def test_update_client(auth_client):
    """Оновлення клієнта"""
    client_data = {'name': 'Старий клієнт'}
    auth_client.post('/api/clients',
                     data=json.dumps(client_data),
                     content_type='application/json')

    update_data = {'name': 'Новий клієнт', 'phone': '+380501111111'}
    response = auth_client.put('/api/clients/1',
                               data=json.dumps(update_data),
                               content_type='application/json')
    assert response.status_code == 200


# ============ ТЕСТИ ОПЕРАЦІЙ ============

def test_income_operation_success(auth_client):
    """Успішне надходження товару"""
    # Створюємо постачальника
    supplier_data = {'name': 'Постачальник'}
    auth_client.post('/api/suppliers',
                     data=json.dumps(supplier_data),
                     content_type='application/json')

    # Створюємо товар
    product_data = {
        'name': 'Товар',
        'quantity': 0,
        'warehouse_number': '1',
        'shelf': 'A',
        'rack': '1'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    # Надходження
    income_data = {
        'product_id': 1,
        'quantity': 10,
        'supplier_id': 1,
        'invoice_number': 'INV-001'
    }
    response = auth_client.post('/operations/income',
                                data=json.dumps(income_data),
                                content_type='application/json')
    assert response.status_code == 200


def test_outcome_operation_success(auth_client):
    """Успішний відпуск товару"""
    # Створюємо клієнта
    client_data = {'name': 'Клієнт'}
    auth_client.post('/api/clients',
                     data=json.dumps(client_data),
                     content_type='application/json')

    # Створюємо товар з кількістю
    product_data = {
        'name': 'Товар',
        'quantity': 20,
        'warehouse_number': '1',
        'shelf': 'B',
        'rack': '2'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    # Відпуск
    outcome_data = {
        'product_id': 1,
        'quantity': 5,
        'client_id': 1,
        'invoice_number': 'OUT-001'
    }
    response = auth_client.post('/operations/outcome',
                                data=json.dumps(outcome_data),
                                content_type='application/json')
    assert response.status_code == 200


def test_outcome_insufficient_quantity(auth_client):
    """Відпуск більше ніж є на складі"""
    client_data = {'name': 'Клієнт'}
    auth_client.post('/api/clients',
                     data=json.dumps(client_data),
                     content_type='application/json')

    product_data = {
        'name': 'Товар',
        'quantity': 5,
        'warehouse_number': '1',
        'shelf': 'C',
        'rack': '3'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    outcome_data = {
        'product_id': 1,
        'quantity': 10,  # Більше ніж є
        'client_id': 1
    }
    response = auth_client.post('/operations/outcome',
                                data=json.dumps(outcome_data),
                                content_type='application/json')
    assert response.status_code == 400


def test_get_operations_list(auth_client):
    """Отримання списку операцій"""
    response = auth_client.get('/api/operations')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


# ============ ТЕСТИ ПЕРЕМІЩЕНЬ ============

def test_product_relocation_success(auth_client):
    """Успішне переміщення товару"""
    # Створюємо товар
    product_data = {
        'name': 'Товар для переміщення',
        'warehouse_number': '1',
        'shelf': 'A',
        'rack': '1'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    # Переміщуємо
    move_data = {
        'product_id': 1,
        'to_warehouse': '2',
        'to_shelf': 'B',
        'to_rack': '2'
    }
    response = auth_client.post('/relocation/move',
                                data=json.dumps(move_data),
                                content_type='application/json')
    assert response.status_code == 200


def test_relocation_to_same_location(auth_client):
    """Переміщення в ту саму локацію (помилка)"""
    product_data = {
        'name': 'Товар',
        'warehouse_number': '1',
        'shelf': 'A',
        'rack': '1'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    move_data = {
        'product_id': 1,
        'to_warehouse': '1',
        'to_shelf': 'A',
        'to_rack': '1'
    }
    response = auth_client.post('/relocation/move',
                                data=json.dumps(move_data),
                                content_type='application/json')
    assert response.status_code == 400


def test_relocation_to_occupied_location(auth_client):
    """Переміщення в зайняту локацію"""
    # Товар 1
    product1 = {
        'name': 'Товар 1',
        'warehouse_number': '1',
        'shelf': 'A',
        'rack': '1'
    }
    auth_client.post('/products',
                     data=json.dumps(product1),
                     content_type='application/json')

    # Товар 2
    product2 = {
        'name': 'Товар 2',
        'warehouse_number': '2',
        'shelf': 'B',
        'rack': '2'
    }
    auth_client.post('/products',
                     data=json.dumps(product2),
                     content_type='application/json')

    # Спроба перемістити товар 1 в локацію товару 2
    move_data = {
        'product_id': 1,
        'to_warehouse': '2',
        'to_shelf': 'B',
        'to_rack': '2'
    }
    response = auth_client.post('/relocation/move',
                                data=json.dumps(move_data),
                                content_type='application/json')
    assert response.status_code == 400


def test_get_movement_history(auth_client):
    """Отримання історії переміщень"""
    response = auth_client.get('/relocation/history')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


# ============ ДОДАТКОВІ ТЕСТИ ============

def test_database_integrity(auth_client):
    """Перевірка цілісності бази даних"""
    # Додаємо товар, постачальника і операцію
    supplier_data = {'name': 'Постачальник'}
    auth_client.post('/api/suppliers',
                     data=json.dumps(supplier_data),
                     content_type='application/json')

    product_data = {
        'name': 'Товар',
        'warehouse_number': '1',
        'shelf': 'A',
        'rack': '1'
    }
    auth_client.post('/products',
                     data=json.dumps(product_data),
                     content_type='application/json')

    income_data = {
        'product_id': 1,
        'quantity': 10,
        'supplier_id': 1
    }
    auth_client.post('/operations/income',
                     data=json.dumps(income_data),
                     content_type='application/json')

    # Намагаємось видалити постачальника з операціями
    response = auth_client.delete('/api/suppliers/1')
    assert response.status_code == 400  # Має бути заборонено


def test_today_operations(auth_client):
    """Перевірка операцій за сьогодні"""
    response = auth_client.get('/api/operations/today')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])