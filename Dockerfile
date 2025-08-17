# Dockerfile для Telegram-бота на aiogram
FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir alembic
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
