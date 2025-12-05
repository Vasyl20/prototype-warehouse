import sys
import os

# Додаємо батьківську директорію до Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Налаштування для pytest
def pytest_configure(config):
    """Викликається перед запуском тестів"""
    print("\n🧪 Початок тестування Warehouse Management System")
    print("=" * 70)

def pytest_sessionfinish(session, exitstatus):
    """Викликається після завершення всіх тестів"""
    print("=" * 70)
    print(f"✅ Тестування завершено з кодом: {exitstatus}")
    if exitstatus == 0:
        print("🎉 Всі тести пройшли успішно!")
    else:
        print("❌ Деякі тести не пройшли. Перевірте вивід вище.")