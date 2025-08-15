# Dockerfile для Telegram-бота на aiogram
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir alembic

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
