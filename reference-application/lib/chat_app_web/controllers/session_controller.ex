defmodule ChatAppWeb.SessionController do
  use ChatAppWeb, :controller

  alias ChatApp.Chat

  def create(conn, %{"name" => name}) do
    {:ok, user} = Chat.create_user(%{name: name})

    conn
    |> put_session(:user_id, user.id)
    |> put_status(:created)
    |> render(:show, user: user)
  end

  def delete(conn, _params) do
    conn
    |> configure_session(drop: true)
    |> send_resp(:no_content, "")
  end
end
