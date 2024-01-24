FROM python:3.10.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /backend/
ADD backend /backend/
ADD requirements.txt /backend/

RUN pip install --upgrade pip && pip install -r requirements.txt
