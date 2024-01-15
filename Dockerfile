FROM python:3.10.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x /app/docker/backend/entrypoint.dev.sh
RUN chmod +x /app/docker/backend/celery-entrypoint.sh

ENV LC_TIME ru_RU.UTF-8