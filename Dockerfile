FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /backend/

RUN apt-get update -y && apt-get -y install locales-all && apt-get -y install gettext

ADD backend /backend/
ADD requirements.txt /backend/

RUN pip install --upgrade pip && pip install -r requirements.txt
