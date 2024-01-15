FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf
COPY conf/nginx.conf /etc/nginx/conf.d

RUN apt-get update && apt-get install -y procps
RUN mkdir -p /app/backend/static
RUN chmod -R 755 /app/backend/static