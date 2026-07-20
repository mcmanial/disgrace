defmodule ChatAppWeb.UserSocket do
  use Phoenix.Socket

  channel "room:*", ChatAppWeb.RoomChannel

  @impl true
  def connect(_params, socket, %{session: %{"user_id" => user_id}}) do
    {:ok, assign(socket, :user_id, user_id)}
  end

  def connect(_params, _socket, _connect_info), do: :error

  @impl true
  def id(socket), do: "user_socket:#{socket.assigns.user_id}"
end
