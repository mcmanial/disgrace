# disgrace

A chat app. Backend-only API (see `CLAUDE.md`) — frontend is handled separately.

## Stack

Python 3.12 / FastAPI / Uvicorn / SQLAlchemy (async) / Postgres, managed with [uv](https://docs.astral.sh/uv/).

## Local development

```
createdb chat_app_dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Config is read from environment variables (see `app/config.py`), with sane
local defaults — `DATABASE_URL`, `SECRET_KEY`, `SOCKET_ORIGINS`.

## Tests

```
createdb chat_app_test
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost/chat_app_test" uv run alembic upgrade head
uv run pytest app/tests
```

## Manual testing

`dev-client/` is a throwaway, unstyled HTML+JS page for exercising the API
by hand — not the real frontend. It currently still speaks the old Phoenix
Channels wire protocol and needs updating for the new WebSocket message
format (`{"event": ..., "payload": ...}`).

## Reference

`reference-application/` is the original Elixir/Phoenix implementation of
this same API, kept around for reference. It is not run or maintained.
