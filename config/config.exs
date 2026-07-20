# This file is responsible for configuring your application
# and its dependencies with the aid of the Config module.
#
# This configuration file is loaded before any dependency and
# is restricted to this project.

# General application configuration
import Config

config :chat_app,
  ecto_repos: [ChatApp.Repo],
  generators: [timestamp_type: :utc_datetime]

# Configure the endpoint
config :chat_app, ChatAppWeb.Endpoint,
  url: [host: "localhost"],
  adapter: Bandit.PhoenixAdapter,
  render_errors: [
    formats: [json: ChatAppWeb.ErrorJSON],
    layout: false
  ],
  pubsub_server: ChatApp.PubSub,
  live_view: [signing_salt: "jGFKchm+"]

# Configure Elixir's Logger
config :logger, :default_formatter,
  format: "$time $metadata[$level] $message\n",
  metadata: [:request_id]

# Use Jason for JSON parsing in Phoenix
config :phoenix, :json_library, Jason

# Configure esbuild (the standalone CLI). NODE_PATH points at deps so JS can
# import the phoenix/phoenix_html/phoenix_live_view packages shipped as deps.
config :esbuild,
  version: "0.25.0",
  chat_app: [
    args:
      ~w(js/app.js --bundle --target=es2022 --outdir=../priv/static/assets --external:/fonts/* --external:/images/*),
    cd: Path.expand("../assets", __DIR__),
    env: %{"NODE_PATH" => Path.expand("../deps", __DIR__)}
  ]

# Configure tailwind (the standalone CLI, v4). daisyUI is loaded as a
# plugin from assets/vendor via the @plugin directive in assets/css/app.css.
config :tailwind,
  version: "4.3.0",
  chat_app: [
    args: ~w(
      --input=assets/css/app.css
      --output=priv/static/assets/app.css
    ),
    cd: Path.expand("..", __DIR__)
  ]

# Import environment specific config. This must remain at the bottom
# of this file so it overrides the configuration defined above.
import_config "#{config_env()}.exs"
