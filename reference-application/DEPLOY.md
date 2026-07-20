# Deploying to a DigitalOcean Ubuntu droplet

A basic, single-box deployment: Postgres, the Phoenix release, and nginx
(TLS termination + reverse proxy) all on one Ubuntu droplet. See the
[Deployment](README.md#deployment) section of the README for background on
the general release mechanics (env vars, `mix release`, migrate) this guide
runs in practice.

This is not a zero-downtime or highly-available setup — it's the minimum to
get the app running behind a real domain with HTTPS.

Run everything below **in one continuous SSH session, in order**. A few
steps generate a password or secret into a shell variable that a later step
reuses directly — if your session drops partway through, just start again
from step 1 (nothing before the systemd step in step 7 is destructive to
rerun).

## 0. Prerequisites

- A DigitalOcean droplet running Ubuntu 24.04 LTS specifically (not 22.04 —
  its `elixir`/`erlang` apt packages are too old for this project), with a
  non-root sudo user set up (DigitalOcean's droplet creation flow can do
  this for you) and SSH access.
- A domain name with an A record already pointing at the droplet's public
  IP (needed for TLS later on).

## 1. Firewall

```
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'   # 80 + 443
sudo ufw enable
```

The app itself will end up bound to `127.0.0.1` only (see
`config/runtime.exs`), so it's never reachable directly from the internet —
only nginx is exposed.

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
directly when building `DATABASE_URL` in step 6.

## 3. Get the code

```
git clone <your-repo-url> ~/disgrace
cd ~/disgrace
```

Everything from here on assumes you're inside this directory.

## 4. Erlang / Elixir

Ubuntu 24.04 ships Elixir 1.16 and Erlang/OTP 26 in its own apt repo —
both well above this project's `elixir "~> 1.15"` floor — so a plain
package install is enough. No compiling, no version manager:

```
sudo apt update
sudo apt install -y erlang elixir

elixir --version
```

The last line should print something like `Elixir 1.16.x (compiled with
Erlang/OTP 26)`. If it ever reports an Elixir version below 1.15 (e.g. you
ended up on 22.04 anyway, or a future Ubuntu release changes what's
packaged), `mix compile` will fail immediately with a clear "Insufficient
Elixir version" error rather than something confusing later — in that
case, install a newer Elixir/Erlang via [asdf](https://asdf-vm.com/) or the
[Erlang Solutions](https://www.erlang-solutions.com/downloads/) apt repo
instead of the two commands above.

## 5. Build the release

```
export SECRET_KEY_BASE=$(mix phx.gen.secret)
mix local.hex --force
mix local.rebar --force

MIX_ENV=prod mix deps.get --only prod
MIX_ENV=prod mix compile
MIX_ENV=prod mix release
```

Releases are built for the same OS/architecture they'll run on, so build
directly on the droplet (or a matching container) — don't copy a release
built on your Mac/dev machine over. `$SECRET_KEY_BASE` stays set for the
rest of this session.

## 6. Environment variables

```
export PHX_HOST=chat.example.com   # replace with your real domain

sudo tee /etc/chat_app.env > /dev/null <<EOF
DATABASE_URL=ecto://chat_app:${DB_PASSWORD}@localhost/chat_app_prod
SECRET_KEY_BASE=${SECRET_KEY_BASE}
PHX_HOST=${PHX_HOST}
PHX_SERVER=true
EOF

sudo chmod 600 /etc/chat_app.env
```

This reuses the `$DB_PASSWORD` and `$SECRET_KEY_BASE` set earlier in this
session, so the file already has real values in it — check with `cat
/etc/chat_app.env` if you want to confirm. See the
[env var table](README.md#deployment) in the README for optional overrides
(`PORT`, `POOL_SIZE`, `SOCKET_ORIGINS`, etc.) — e.g. set `SOCKET_ORIGINS` if
the frontend is served from a different domain than the API.

## 7. Migrate and start the service

```
set -a; source /etc/chat_app.env; set +a
~/disgrace/_build/prod/rel/chat_app/bin/chat_app eval "ChatApp.Release.migrate()"
```

Now create the systemd unit:

```
sudo tee /etc/systemd/system/chat_app.service > /dev/null <<EOF
[Unit]
Description=chat_app Phoenix release
After=network.target postgresql.service

[Service]
Type=exec
User=$(whoami)
WorkingDirectory=$HOME/disgrace
EnvironmentFile=/etc/chat_app.env
ExecStart=$HOME/disgrace/_build/prod/rel/chat_app/bin/chat_app start
ExecStop=$HOME/disgrace/_build/prod/rel/chat_app/bin/chat_app stop
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

It should be listening on `127.0.0.1:4000`.

## 8. nginx reverse proxy + TLS

```
sudo apt install -y nginx certbot python3-certbot-nginx

sudo tee /etc/nginx/sites-available/chat_app > /dev/null <<EOF
server {
    listen 80;
    server_name $PHX_HOST;

    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_http_version 1.1;

        # Required for Phoenix Channels (WebSocket upgrade)
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

sudo certbot --nginx -d $PHX_HOST
```

(certbot edits the nginx config in place to add the `listen 443 ssl` block
and the HTTP→HTTPS redirect.) The `Upgrade`/`Connection` headers above are
what make WebSocket channel connections work through the proxy — without
them, REST endpoints work fine but `RoomChannel` joins will fail.

## 9. Verify

```
curl -i https://$PHX_HOST/api/rooms
```

Should return `401 {"error":"unauthenticated"}` (correct — you're not
logged in, but it proves the app, nginx, and TLS are all wired up).

## Redeploying after code changes

A separate, repeatable procedure for later — not part of the initial setup
above. Run as the same deploy user, from a fresh session if you like:

```
cd ~/disgrace
git pull
MIX_ENV=prod mix deps.get --only prod
MIX_ENV=prod mix compile
MIX_ENV=prod mix release --overwrite

sudo systemctl stop chat_app
set -a; source /etc/chat_app.env; set +a
~/disgrace/_build/prod/rel/chat_app/bin/chat_app eval "ChatApp.Release.migrate()"
sudo systemctl start chat_app
```

This causes brief downtime during the restart — acceptable for a basic
setup, but worth knowing if you need zero-downtime deploys later.
