.PHONY: up down run test lint format check

up:
	docker compose -f backend/docker-compose.yml up -d

down:
	docker compose -f backend/docker-compose.yml down

run:
	cd backend && uv run uvicorn app.main:app --reload --port 8080

test:
	cd backend && uv run pytest -c pyproject.toml ../tests

lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run black .

check:
	cd backend && uv run ruff check .
	cd backend && uv run black --check .
	cd backend && uv run pytest -c pyproject.toml ../tests
