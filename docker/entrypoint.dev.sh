#!/bin/sh

until cd /app/backend
do
    echo "Waiting for server volume..."
done


until python manage.py migrate
do
    echo "Waiting for db to be ready..."
    sleep 2
done


python manage.py collectstatic --noinput
# python manage.py search_index --rebuild -f

uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload