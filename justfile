compose_file := "./docker-compose.local.yaml"

init:
    uv sync

check:
    set -e; \
    uv run ruff format; \
    uv run ruff check --fix; \
    uv run mypy backend/ tests/; \
    uv run python .claude/hooks/guard_layers.py

guard-paths:
    uv run python .claude/hooks/guard_paths.py

status:
    @echo "branch: $(git branch --show-current)"
    @git diff --stat HEAD 2>/dev/null || true
    @echo "---"
    @docker compose -f {{ compose_file }} ps 2>/dev/null || echo "docker: not running"

test:
    uv run nox -s integration

test-adapters:
    uv run nox -s adapters

test-unit:
    uv run nox -s unit

test-all:
    uv run nox --tags tests

run svc="api":
    uv run backend {{ svc }}

start +svc:
    docker compose -f {{ compose_file }} up -d --force-recreate --build {{ svc }}

stop:
    docker compose -f {{ compose_file }} stop

delete: stop
    docker compose -f {{ compose_file }} rm -f -v
    docker volume rm psql_data

logs:
    docker compose -f {{ compose_file }} logs

migrate:
    uv run backend alembic upgrade head

migration msg:
    uv run backend alembic revision --autogenerate -m "{{ msg }}"
