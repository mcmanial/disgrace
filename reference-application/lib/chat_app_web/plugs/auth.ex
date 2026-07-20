defmodule ChatAppWeb.Plugs.Auth do
  import Plug.Conn

  alias ChatApp.Chat

  def fetch_current_user(conn, _opts) do
    case get_session(conn, :user_id) do
      nil ->
        assign(conn, :current_user, nil)

      user_id ->
        assign(conn, :current_user, Chat.get_user!(user_id))
    end
  end

  def require_authenticated_user(conn, _opts) do
    if conn.assigns[:current_user] do
      conn
    else
      conn
      |> put_status(:unauthorized)
      |> Phoenix.Controller.json(%{error: "unauthenticated"})
      |> halt()
    end
  end
end
