FROM python:3.9
WORKDIR /app
# Дальнейшие инструкции будут выполняться в директории /app
COPY requirements.txt .

# Выполнить в текущей директории команду терминала
# для установки зависимостей.
RUN pip install -r requirements.txt --no-cache-dir

# Скопировать всё необходимое содержимое 
# той директории локального компьютера, где сохранён Dockerfile,
# в текущую рабочую директорию образа — /app.
COPY . .
# Выполняем миграции
RUN python manage.py migrate
# Собираем статические файлы
RUN python manage.py collectstatic --noinput
# Команда для запуска Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.wsgi:application"]