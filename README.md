# disgrace

A chat app.

## Elixir / Phoenix backend, Postgres

Backend-only API (see `CLAUDE.md`). Frontend is handled separately.

    mix deps.get
    mix ecto.create
    mix ecto.migrate
    mix phx.server

## Deployment

For a concrete, from-scratch walkthrough (DigitalOcean Ubuntu droplet,
Postgres, systemd, nginx + TLS), see [DEPLOY.md](DEPLOY.md). What follows
here is the general release mechanics any hosting target needs.

Requires a reachable Postgres instance. This app builds as a standard
[Elixir release](https://hexdocs.pm/mix/Mix.Tasks.Release.html) — no external
runtime dependencies (Erlang/Elixir are bundled into the release).

### 1. Set required environment variables

| Variable         | Required | Example                                    |
|-------------------|----------|---------------------------------------------|
| `DATABASE_URL`     | yes      | `ecto://USER:PASS@HOST/chat_app_prod`        |
| `SECRET_KEY_BASE`  | yes      | output of `mix phx.gen.secret`               |
| `PHX_HOST`         | yes      | `chat.example.com`                           |
| `PHX_SERVER`       | yes      | `true` (tells the release to start the endpoint) |
| `PORT`             | no       | `4000` (default)                             |
| `POOL_SIZE`        | no       | `10` (default)                               |
| `ECTO_IPV6`        | no       | `true`, if the DB is only reachable over IPv6 |

### 2. Build the release

    MIX_ENV=prod mix deps.get --only prod
    MIX_ENV=prod mix compile
    MIX_ENV=prod mix release

This produces a self-contained build under `_build/prod/rel/chat_app`.

### 3. Migrate and start

    _build/prod/rel/chat_app/bin/chat_app eval "ChatApp.Release.migrate()"
    PHX_SERVER=true _build/prod/rel/chat_app/bin/chat_app start

Run the `eval` migrate step again after deploying any release that adds new
migrations. Use `bin/chat_app start_iex` instead of `start` to boot with an
attached remote shell.
