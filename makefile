loc_containers := db backend celery rabbit

build:
	docker-compose up --build --remove-orphans -d \
    && docker exec -it goodwin_backend python3 manage.py migrate \
    && docker-compose up
rebuild:
	docker-compose -f docker-compose.yml up -d --build --force-recreate
	docker image prune -f
rebuild-loc:
	docker-compose up -d --build --force-recreate $(loc_containers)
	docker image prune -f

up:
	docker-compose -f docker-compose.yml up -d
up-loc:
	docker-compose -f docker-compose.yml up -d $(loc_containers)
down:
	docker-compose -f docker-compose.yml down
reup-loc:
	docker-compose -f docker-compose.yml down
	docker-compose -f docker-compose.yml up -d $(loc_containers)
reup:
	docker-compose -f docker-compose.yml down
	docker-compose -f docker-compose.yml up -d

start:
	docker-compose -f docker-compose.yml start
stop:
	docker-compose -f docker-compose.yml stop

restart:
	docker-compose -f docker-compose.yml stop
	docker-compose -f docker-compose.yml up -d
restart-loc:
	docker-compose -f docker-compose.yml stop
	docker-compose -f docker-compose.yml up -d $(loc_containers)

makemigrations:
	docker exec -it goodwin_backend python3 backend/manage.py makemigrations
migrate:
	docker exec -it goodwin_backend python3 backend/manage.py migrate
collectstatic:
	docker exec -it goodwin_backend python3 backend/manage.py collectstatic
