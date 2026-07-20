defmodule ChatAppWeb.RoomController do
  use ChatAppWeb, :controller

  alias ChatApp.Chat

  def index(conn, _params) do
    rooms = Chat.list_rooms()
    render(conn, :index, rooms: rooms)
  end

  def create(conn, %{"name" => name}) do
    case Chat.create_room(%{name: name}) do
      {:ok, room} ->
        conn
        |> put_status(:created)
        |> render(:show, room: room)

      {:error, changeset} ->
        conn
        |> put_status(:unprocessable_entity)
        |> render(:error, changeset: changeset)
    end
  end
end
