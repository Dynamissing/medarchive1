.PHONY: up down migrate import-services import-archive run-tests setup test lint format tree

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	docker compose run --rm backend alembic upgrade head

import-services:
	docker compose run --rm backend python ../scripts/import_services.py $(FILE)

import-archive:
	docker compose run --rm backend python ../scripts/import_archive.py $(FILE)

run-tests:
	docker compose run --rm backend pytest -q

setup: up migrate

test: run-tests

lint:
	@echo "Bootstrap phase: lint commands are not wired yet."

format:
	@echo "Bootstrap phase: format commands are not wired yet."

tree:
	@tree -L 3
