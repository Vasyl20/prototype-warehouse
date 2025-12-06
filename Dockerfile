# Використовуємо офіційний Python образ
FROM python:3.11-slim

# Встановлюємо робочу директорію
WORKDIR /app

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копіюємо файл залежностей
COPY requirements.txt .

# Встановлюємо Python залежності
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь проект
COPY . .

# Створюємо директорію для бази даних
RUN mkdir -p /app/data

# Відкриваємо порт
EXPOSE 5000

# Встановлюємо змінні середовища
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Запускаємо додаток
CMD ["python", "app.py"]