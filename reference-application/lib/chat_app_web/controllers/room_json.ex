defmodule ChatAppWeb.RoomJSON do
  alias ChatApp.Chat.Room

  def index(%{rooms: rooms}), do: %{data: for(room <- rooms, do: data(room))}

  def show(%{room: room}), do: data(room)

  def error(%{changeset: changeset}) do
    %{errors: Ecto.Changeset.traverse_errors(changeset, fn {msg, _opts} -> msg end)}
  end

  def data(%Room{} = room) do
    %{id: room.id, name: room.name}
  end
end
