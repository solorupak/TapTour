.DEFAULT_GOAL := help
COMPOSE := docker compose
MANAGE := $(COMPOSE) exec web python manage.py
ARGS ?=

.PHONY: help setup build up down restart logs ps check makemigrations migrate shell superuser test dbshell manage

help:
	@echo "Docker: setup build up down restart logs ps"
	@echo "Django: check makemigrations migrate shell superuser test dbshell"
	@echo 'Extra arguments: make test ARGS="apps.content"'
	@echo 'Any Django command: make manage ARGS="showmigrations"'

setup:
	@test -f .env || cp .env.example .env

build:
	$(COMPOSE) build

start: setup
	$(COMPOSE) up -d --build

stop:
	$(COMPOSE) down

restart:
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f $(ARGS)

ps:
	$(COMPOSE) ps

check makemigrations migrate shell test:
	$(MANAGE) $@ $(ARGS)

superuser:
	$(MANAGE) createsuperuser $(ARGS)

dbshell:
	$(COMPOSE) exec db sh -c 'exec psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

manage:
	$(MANAGE) $(ARGS)
