# Project: Chat App Backend

Backend-only API. Frontend is handled separately by another dev — do not build UI, templates, or htmx.
(A throwaway `dev-client/` HTML+JS page exists purely for manually exercising the API locally — not the real frontend.)

## Stack
- Language: Python 3.12, managed with `uv` (not pip/venv directly — `uv add`, `uv run`, `uv sync`)
- Web framework: FastAPI, served by Uvicorn (ASGI)
- DB: PostgreSQL, via SQLAlchemy 2.0 (async, `asyncpg` driver)
- Migrations: Alembic (`alembic/env.py` is wired to `app.db.Base.metadata` and `app.config.settings`, not `alembic.ini`, for autogenerate)
- Realtime: native FastAPI `WebSocket` routes (no Socket.IO/Channels library) — a single in-process `RoomConnectionManager` (`app/ws.py`) tracks connections per room and broadcasts
- Auth: session-based, via Starlette's `SessionMiddleware` (signed cookie, `itsdangerous`) — not JWT, sessions are revocable and avoid token-in-localStorage exposure
- WebSocket auth: authenticated at connect time by reading `websocket.session["user_id"]` (populated from the cookie during the ASGI handshake), not per-message
- CORS: any `localhost`/`127.0.0.1` origin is allowed with credentials (see `app/config.py` `socket_origins`) — needed since the dev client / real frontend run on a different port than the API

## Structure
```
app/
  main.py            # FastAPI app instance, middleware, router wiring
  config.py           # pydantic-settings (env vars: DATABASE_URL, SECRET_KEY, SOCKET_ORIGINS)
  db.py                # async engine/session, declarative Base
  models.py           # User, Room, Message (SQLAlchemy ORM)
  schemas.py          # Pydantic request/response models
  auth.py              # get_current_user dependency (HTTP), get_current_user_ws (WebSocket)
  ws.py                 # /ws/rooms/{room_id} + RoomConnectionManager (join/broadcast/presence)
  routers/
    sessions.py       # POST/DELETE /api/session
    rooms.py           # GET/POST /api/rooms
    messages.py       # GET /api/rooms/{room_id}/messages (paginated: ?limit=&before_id=)
  tests/
alembic/               # migrations
dev-client/            # throwaway manual-testing HTML+JS page, not the real frontend
reference-application/ # the original Elixir/Phoenix implementation, kept for reference only — not run, not maintained
```

## Schema (initial)
- `rooms(id, name)`
- `messages(id, room_id, user_id, body, created_at)`
- `users(id, name)`

## Conventions
- Message history loads via REST (`GET /api/rooms/:id/messages`) on joining a room; live messages come through the WebSocket after.
- "Who's online" presence is implemented (`presence_state` on join, `presence_diff` broadcasts) — in-memory per-process, not distributed. Fine for a single-instance deploy; would need rework (e.g. Redis pub/sub) if ever run with multiple app processes/workers.
- Don't add features not explicitly requested (no read receipts, typing indicators, etc. unless asked).
- SQL: Postgres only, no other DB assumptions.
- Use `uv add <pkg>` to add dependencies (updates `pyproject.toml` + `uv.lock`), `uv run <cmd>` to run anything in the project's environment. Don't use bare `pip`/`python -m venv`.
- Run tests with `uv run pytest app/tests`. Tests hit a real Postgres db (`chat_app_test` locally) — no mocking the database.

## Why the rewrite from Elixir/Phoenix
The original implementation (see `reference-application/`) worked, but deployment kept hitting toolchain friction on a small (512MB) DigitalOcean droplet: compiling Erlang/OTP from source ran out of memory, and once that was fixed, apt's packaged Elixir version was too old. Python was chosen to sidestep that entire class of problem — the target deploy OS ships a usable `python3` already, and `uv` manages exact interpreter/dependency versions without ever compiling anything.
