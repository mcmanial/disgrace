defmodule ChatAppWeb.RoomChannelTest do
  use ChatAppWeb.ChannelCase, async: true

  alias ChatApp.Chat
  alias ChatAppWeb.UserSocket

  setup do
    {:ok, user} = Chat.create_user(%{name: "mike"})
    {:ok, room} = Chat.create_room(%{name: "general"})

    {:ok, socket} = connect(UserSocket, %{}, connect_info: %{session: %{"user_id" => user.id}})
    {:ok, _reply, socket} = subscribe_and_join(socket, "room:#{room.id}", %{})

    %{socket: socket, user: user, room: room}
  end

  test "connect/3 rejects sockets without a session user_id" do
    assert :error = connect(UserSocket, %{}, connect_info: %{session: %{}})
  end

  test "new_message broadcasts and persists the message", %{
    socket: socket,
    user: user,
    room: room
  } do
    push(socket, "new_message", %{"body" => "hello"})
    assert_broadcast "new_message", %{body: "hello", user_id: user_id, room_id: room_id}
    assert user_id == user.id
    assert room_id == room.id

    assert [%{body: "hello"}] = Chat.list_messages(room.id)
  end

  test "pushes presence_state with the joining user after join", %{user: user} do
    user_id = to_string(user.id)
    assert_push "presence_state", %{^user_id => %{metas: [%{name: "mike"}]}}
  end

  test "broadcasts presence_diff when another user joins the room", %{room: room} do
    {:ok, other_user} = Chat.create_user(%{name: "other"})

    {:ok, socket2} =
      connect(UserSocket, %{}, connect_info: %{session: %{"user_id" => other_user.id}})

    {:ok, _reply, _socket2} = subscribe_and_join(socket2, "room:#{room.id}", %{})

    other_id = to_string(other_user.id)
    assert_broadcast "presence_diff", %{joins: %{^other_id => _}}
  end
end
