# Deploying to a DigitalOcean Ubuntu droplet

A basic, single-box deployment: Postgres, the Phoenix release, and nginx
(TLS termination + reverse proxy) all on one Ubuntu droplet. See the
[Deployment](README.md#deployment) section of the README first for the
release mechanics (env vars, build, migrate) this guide builds on top of.

This is not a zero-downtime or highly-available setup — it's the minimum to
get the app running behind a real domain with HTTPS.

## 0. Prerequisites

- A DigitalOcean droplet running Ubuntu 22.04 or 24.04 LTS, with a non-root
  sudo user set up (DigitalOcean's droplet creation flow can do this for
  you) and SSH access.
- A domain name with an A record pointing at the droplet's public IP. TLS
  (step 6) will not work without this.
- This guide assumes a small/medium droplet (1-2GB RAM). If you're on the
  smallest (512MB-1GB) droplet, add swap before compiling (step 3) or the
  build may get OOM-killed.

All commands below are run as your sudo user on the droplet, unless noted.

## 1. Firewall

```
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # 80 + 443
sudo ufw enable
```

The app itself binds to `127.0.0.1` only (see `config/runtime.exs`) once
`BIND_ALL` is left unset, so it's never reachable directly from the
internet — only nginx is exposed.

## 2. PostgreSQL

```
sudo apt update
sudo apt install -y postgresql

sudo -u postgres createuser --pwprompt chat_app
sudo -u postgres createdb -O chat_app chat_app_prod
```

Note the password you set — it goes into `DATABASE_URL` in step 5.

## 3. Erlang / Elixir

This project pins exact versions in `.tool-versions`. Install them with
[asdf](https://asdf-vm.com/):

```
sudo apt install -y build-essential autoconf m4 libncurses-dev \
  libssl-dev unixodbc-dev libgl1-mesa-dev libglu1-mesa-dev libpng-dev \
  libssh-dev unzip zip git curl

git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.15.0
echo '. "$HOME/.asdf/asdf.sh"' >> ~/.bashrc
source ~/.asdf/asdf.sh

asdf plugin add erlang
asdf plugin add elixir

cd /path/to/disgrace   # after cloning the repo, see step 4
asdf install           # reads .tool-versions
```

Erlang's build from source takes a while (5-10 minutes) — this is normal.

## 4. Get the code and build a release

```
git clone <your-repo-url> disgrace
cd disgrace

export SECRET_KEY_BASE=$(mix phx.gen.secret)   # save this, see step 5
mix local.hex --force
mix local.rebar --force

MIX_ENV=prod mix deps.get --only prod
MIX_ENV=prod mix compile
MIX_ENV=prod mix release
```

Releases are built for the same OS/architecture they'll run on, so build
directly on the droplet (or a matching container) — don't copy a release
built on your Mac/dev machine over.

## 5. Environment variables

Create `/etc/chat_app.env` (root-only, holds secrets):

```
sudo tee /etc/chat_app.env > /dev/null <<'EOF'
DATABASE_URL=ecto://chat_app:YOUR_DB_PASSWORD@localhost/chat_app_prod
SECRET_KEY_BASE=YOUR_SECRET_KEY_BASE
PHX_HOST=chat.example.com
PHX_SERVER=true
EOF

sudo chmod 600 /etc/chat_app.env
```

Fill in the DB password from step 2 and the `SECRET_KEY_BASE` from step 4.
`PHX_HOST` must match the domain pointing at this droplet. See the
[env var table](README.md#deployment) in the README for the full list
(`PORT`, `POOL_SIZE`, `SOCKET_ORIGINS`, etc.) if you need to override
defaults — e.g. set `SOCKET_ORIGINS` if the frontend is served from a
different domain than the API.

## 6. Migrate and set up the systemd service

Run migrations once per deploy (this and future ones):

```
/home/YOUR_USER/disgrace/_build/prod/rel/chat_app/bin/chat_app eval \
  "ChatApp.Release.migrate()"
```

(This one-off run needs the env vars too — either `source /etc/chat_app.env`
first, or run it via `systemd-run` with the same EnvironmentFile. Easiest is
to start the service once via step 7 below, then re-run migrations through
`systemctl` after future deploys — see step 8.)

Create `/etc/systemd/system/chat_app.service`:

```
sudo tee /etc/systemd/system/chat_app.service > /dev/null <<'EOF'
[Unit]
Description=chat_app Phoenix release
After=network.target postgresql.service

[Service]
Type=exec
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/disgrace
EnvironmentFile=/etc/chat_app.env
ExecStart=/home/YOUR_USER/disgrace/_build/prod/rel/chat_app/bin/chat_app start
ExecStop=/home/YOUR_USER/disgrace/_build/prod/rel/chat_app/bin/chat_app stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Replace `YOUR_USER` (both the `User=` line and the paths) with your actual
sudo username, then:

```
sudo systemctl daemon-reload
sudo systemctl enable --now chat_app
sudo systemctl status chat_app
journalctl -u chat_app -f   # tail logs
```

It should be listening on `127.0.0.1:4000`.

## 7. nginx reverse proxy + TLS

```
sudo apt install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/chat_app`:

```
sudo tee /etc/nginx/sites-available/chat_app > /dev/null <<'EOF'
server {
    listen 80;
    server_name chat.example.com;

    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_http_version 1.1;

        # Required for Phoenix Channels (WebSocket upgrade)
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/chat_app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Replace `chat.example.com` with your real domain, then get a certificate
(certbot edits the nginx config in place to add the `listen 443 ssl` block
and redirect):

```
sudo certbot --nginx -d chat.example.com
```

The `Upgrade`/`Connection` headers above are what make WebSocket channel
connections work through the proxy — without them, REST endpoints work
fine but `RoomChannel` joins will fail.

## 8. Verify

```
curl -i https://chat.example.com/api/rooms
```

Should return `401 {"error":"unauthenticated"}` (correct — you're not
logged in, but it proves the app, nginx, and TLS are all wired up).

## Redeploying after code changes

```
cd /home/YOUR_USER/disgrace
git pull
MIX_ENV=prod mix deps.get --only prod
MIX_ENV=prod mix compile
MIX_ENV=prod mix release --overwrite

sudo systemctl stop chat_app
_build/prod/rel/chat_app/bin/chat_app eval "ChatApp.Release.migrate()"
sudo systemctl start chat_app
```

This causes brief downtime during the restart — acceptable for a basic
setup, but worth knowing if you need zero-downtime deploys later.
