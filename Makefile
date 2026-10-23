-include .env
FRONTEND_PORT ?= 8081

.PHONY: up down stop start restart logs ps stats once clean

up:        ## Build and start everything in the background
	docker compose up -d --build

down:      ## Stop and remove containers (model stays cached)
	docker compose down

stop:      ## Pause the demo, keep containers
	docker compose stop

start:     ## Resume after stop
	docker compose start

restart: down up

logs:      ## Follow logs from all services
	docker compose logs -f --tail=50

ps:
	docker compose ps

stats:     ## Live CPU and memory per container
	docker stats $$(docker compose ps -q)

once:      ## Trigger one extra trace by hand
	curl -s "http://127.0.0.1:$(FRONTEND_PORT)/fact?topic=saunas"; echo

clean:     ## Remove everything including the downloaded model
	docker compose down -v --rmi local
