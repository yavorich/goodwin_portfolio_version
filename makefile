loc_containers := db backend celery rabbit

build:
	docker-compose up --build --remove-orphans -d \
    && docker exec -it goodwin_backend python3 manage.py migrate \
    && docker exec -it goodwin_backend python3 manage.py compilemessages \
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


check:
	docker exec -it goodwin_backend python3 manage.py check
makemigrations:
	docker exec -it goodwin_backend python3 manage.py makemigrations
migrate:
	docker exec -it goodwin_backend python3 manage.py migrate
collectstatic:
	docker exec -it goodwin_backend python3 manage.py collectstatic
createsuperuser:
	docker exec -it goodwin_backend python3 manage.py createsuperuser
shell:
	docker exec -it goodwin_backend python3 manage.py shell

makemessages:
	docker exec -it goodwin_backend python3 manage.py makemessages -a
compilemessages:
	docker exec -it goodwin_backend python3 manage.py compilemessages
