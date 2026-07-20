defmodule ChatAppWeb.Router do
  use ChatAppWeb, :router

  import ChatAppWeb.Plugs.Auth

  pipeline :api do
    plug :accepts, ["json"]
    plug :fetch_session
    plug :fetch_current_user
  end

  pipeline :authenticated do
    plug :require_authenticated_user
  end

  scope "/api", ChatAppWeb do
    pipe_through :api

    post "/session", SessionController, :create
    delete "/session", SessionController, :delete
  end

  scope "/api", ChatAppWeb do
    pipe_through [:api, :authenticated]

    resources "/rooms", RoomController, only: [:index, :create]
    get "/rooms/:room_id/messages", MessageController, :index
  end

  # Enable LiveDashboard in development
  if Application.compile_env(:chat_app, :dev_routes) do
    # If you want to use the LiveDashboard in production, you should put
    # it behind authentication and allow only admins to access it.
    # If your application does not have an admins-only section yet,
    # you can use Plug.BasicAuth to set up some basic authentication
    # as long as you are also using SSL (which you should anyway).
    import Phoenix.LiveDashboard.Router

    scope "/dev" do
      pipe_through [:fetch_session, :protect_from_forgery]

      live_dashboard "/dashboard", metrics: ChatAppWeb.Telemetry
    end
  end
end
