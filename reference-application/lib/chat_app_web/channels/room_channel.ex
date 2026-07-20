defmodule ChatAppWeb.RoomChannel do
  use ChatAppWeb, :channel

  alias ChatApp.Chat
  alias ChatAppWeb.Presence

  @impl true
  def join("room:" <> room_id, _params, socket) do
    room_id = String.to_integer(room_id)
    Chat.get_room!(room_id)
    send(self(), :after_join)
    {:ok, assign(socket, :room_id, room_id)}
  rescue
    Ecto.NoResultsError -> {:error, %{reason: "not_found"}}
  end

  @impl true
  def handle_info(:after_join, socket) do
    user = Chat.get_user!(socket.assigns.user_id)

    {:ok, _} =
      Presence.track(socket, to_string(user.id), %{
        name: user.name,
        online_at: System.system_time(:second)
      })

    push(socket, "presence_state", Presence.list(socket))
    {:noreply, socket}
  end

  @impl true
  def handle_in("new_message", %{"body" => body}, socket) do
    attrs = %{body: body, room_id: socket.assigns.room_id, user_id: socket.assigns.user_id}

    case Chat.create_message(attrs) do
      {:ok, message} ->
        broadcast!(socket, "new_message", %{
          id: message.id,
          body: message.body,
          room_id: message.room_id,
          user_id: message.user_id,
          created_at: message.created_at
        })

        {:noreply, socket}

      {:error, changeset} ->
        {:reply, {:error, %{errors: changeset_errors(changeset)}}, socket}
    end
  end

  defp changeset_errors(changeset) do
    Ecto.Changeset.traverse_errors(changeset, fn {msg, _opts} -> msg end)
  end
end
