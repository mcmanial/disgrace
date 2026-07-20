defmodule ChatAppWeb.MessageControllerTest do
  use ChatAppWeb.ConnCase, async: true

  alias ChatApp.Chat

  defp log_in(conn, name \\ "mike") do
    post(conn, ~p"/api/session", %{"name" => name})
  end

  test "GET /api/rooms/:room_id/messages returns message history", %{conn: conn} do
    {:ok, user} = Chat.create_user(%{name: "mike"})
    {:ok, room} = Chat.create_room(%{name: "general"})
    {:ok, _message} = Chat.create_message(%{body: "hi", room_id: room.id, user_id: user.id})

    conn = conn |> log_in() |> get(~p"/api/rooms/#{room.id}/messages")
    assert [%{"body" => "hi", "room_id" => room_id}] = json_response(conn, 200)["data"]
    assert room_id == room.id
  end

  test "requires authentication", %{conn: conn} do
    conn = get(conn, ~p"/api/rooms/1/messages")
    assert json_response(conn, 401)
  end
end
