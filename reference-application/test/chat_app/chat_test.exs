defmodule ChatApp.ChatTest do
  use ChatApp.DataCase, async: true

  alias ChatApp.Chat

  test "create_user/1 with valid data creates a user" do
    assert {:ok, user} = Chat.create_user(%{name: "mike"})
    assert user.name == "mike"
  end

  test "create_user/1 with invalid data returns error changeset" do
    assert {:error, changeset} = Chat.create_user(%{name: nil})
    assert %{name: ["can't be blank"]} = errors_on(changeset)
  end

  test "create_room/1 and list_rooms/0" do
    assert {:ok, room} = Chat.create_room(%{name: "general"})
    assert Chat.list_rooms() == [room]
  end

  test "create_message/1 and list_messages/2 returns oldest-first, most recent within limit" do
    {:ok, user} = Chat.create_user(%{name: "mike"})
    {:ok, room} = Chat.create_room(%{name: "general"})

    {:ok, m1} = Chat.create_message(%{body: "first", room_id: room.id, user_id: user.id})
    {:ok, m2} = Chat.create_message(%{body: "second", room_id: room.id, user_id: user.id})
    {:ok, m3} = Chat.create_message(%{body: "third", room_id: room.id, user_id: user.id})

    assert Enum.map(Chat.list_messages(room.id), & &1.id) == [m1.id, m2.id, m3.id]
    assert Enum.map(Chat.list_messages(room.id, limit: 2), & &1.id) == [m2.id, m3.id]
    assert Enum.map(Chat.list_messages(room.id, before_id: m3.id), & &1.id) == [m1.id, m2.id]
  end
end
