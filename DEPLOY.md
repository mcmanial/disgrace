# Deploying to a DigitalOcean Ubuntu droplet

A basic, single-box deployment: Postgres, the FastAPI app (via Uvicorn), and
nginx (TLS termination + reverse proxy) all on one Ubuntu droplet.

This is not a zero-downtime or highly-available setup — it's the minimum to
get the app running behind a real domain with HTTPS.

Run everything below **in one continuous SSH session, in order**. A few
steps generate a password or secret into a shell variable that a later step
reuses directly — if your session drops partway through, just start again
from step 1 (nothing before the systemd step in step 6 is destructive to
rerun).

## 0. Prerequisites

- A DigitalOcean droplet running Ubuntu 24.04 LTS, with a non-root sudo
  user set up (DigitalOcean's droplet creation flow can do this for you)
  and SSH access.
- A domain name with an A record already pointing at the droplet's public
  IP (needed for TLS later on).

## 1. Firewall

```
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # 80 + 443
sudo ufw enable
```

The app itself will end up bound to `127.0.0.1` only, so it's never
reachable directly from the internet — only nginx is exposed.

## 2. PostgreSQL

```
sudo apt update
sudo apt install -y postgresql

DB_PASSWORD=$(openssl rand -hex 16)
echo "Generated DB password (save it somewhere safe too): $DB_PASSWORD"

sudo -u postgres psql -c "CREATE USER chat_app WITH PASSWORD '$DB_PASSWORD';"
sudo -u postgres createdb -O chat_app chat_app_prod
```

`$DB_PASSWORD` stays set for the rest of this session and gets used
directly when building `DATABASE_URL` in step 5.

## 3. Get the code

```
git clone <your-repo-url> ~/disgrace
cd ~/disgrace
```

Everything from here on assumes you're inside this directory.

## 4. Python / dependencies

Install [uv](https://docs.astral.sh/uv/) — it downloads a prebuilt Python
3.12 itself (matching `requires-python` in `pyproject.toml`) rather than
relying on whatever the OS happens to ship, and installs dependencies from
`uv.lock`. Nothing gets compiled:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

uv sync --frozen
```

`uv sync --frozen` fails loudly instead of silently re-resolving if
`uv.lock` and `pyproject.toml` are out of sync — that's intentional here.

## 5. Environment variables

```
export DOMAIN=chat.example.com   # replace with your real domain
SECRET_KEY=$(openssl rand -hex 32)

sudo tee /etc/chat_app.env > /dev/null <<EOF
DATABASE_URL=postgresql+asyncpg://chat_app:${DB_PASSWORD}@localhost/chat_app_prod
SECRET_KEY=${SECRET_KEY}
SOCKET_ORIGINS=https://${DOMAIN}
EOF

sudo chmod 600 /etc/chat_app.env
```

This reuses `$DB_PASSWORD` from step 2. `SOCKET_ORIGINS` is the allowlist
for cross-origin cookie-authenticated requests (REST and WebSocket) — set
it to wherever the actual frontend is served from; use a comma-separated
list if there's more than one (e.g. a staging and a production frontend).

## 6. Migrate and start the service

```
set -a; source /etc/chat_app.env; set +a
uv run alembic upgrade head
```

Now create the systemd unit:

```
sudo tee /etc/systemd/system/chat_app.service > /dev/null <<EOF
[Unit]
Description=chat_app FastAPI service
After=network.target postgresql.service

[Service]
Type=exec
User=$(whoami)
WorkingDirectory=$HOME/disgrace
EnvironmentFile=/etc/chat_app.env
ExecStart=$HOME/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now chat_app
sudo systemctl status chat_app
journalctl -u chat_app -f   # tail logs, Ctrl-C to stop tailing
```

It should be listening on `127.0.0.1:8000`.

Deliberately **no `--workers` flag**: room presence and the WebSocket
connection registry (`app/ws.py`) live in a single process's memory. Adding
Uvicorn workers would silently split users across separate processes that
can't see each other — presence and broadcast would start missing people
with no error. If this ever needs to scale beyond one process, that state
needs to move to something shared (e.g. Redis pub/sub) first.

## 7. nginx reverse proxy + TLS

```
sudo apt install -y nginx certbot python3-certbot-nginx

sudo tee /etc/nginx/sites-available/chat_app > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;

        # Required for the WebSocket routes (chat, presence)
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/chat_app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

sudo certbot --nginx -d $DOMAIN
```

(certbot edits the nginx config in place to add the `listen 443 ssl` block
and the HTTP→HTTPS redirect.) The `Upgrade`/`Connection` headers above are
what make WebSocket connections work through the proxy — without them,
REST endpoints work fine but `/ws/rooms/{id}` connections will fail.

## 8. Verify

```
curl -i https://$DOMAIN/api/rooms
```

Should return `401 {"detail":"unauthenticated"}` (correct — you're not
logged in, but it proves the app, nginx, and TLS are all wired up).

## Redeploying after code changes

A separate, repeatable procedure for later — not part of the initial setup
above. Run as the same deploy user, from a fresh session if you like:

```
cd ~/disgrace
git pull
uv sync --frozen

sudo systemctl stop chat_app
set -a; source /etc/chat_app.env; set +a
uv run alembic upgrade head
sudo systemctl start chat_app
```

This causes brief downtime during the restart — acceptable for a basic
setup, but worth knowing if you need zero-downtime deploys later.
