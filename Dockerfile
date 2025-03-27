# Используем официальный образ Python
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения в образ
COPY . .

# Устанавливаем gunicorn
RUN pip install gunicorn

# Открываем порт, который будет использоваться приложением
EXPOSE 5000

# Команда для запуска приложения с помощью gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]