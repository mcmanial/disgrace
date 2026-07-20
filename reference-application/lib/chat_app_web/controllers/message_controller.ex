defmodule ChatAppWeb.MessageController do
  use ChatAppWeb, :controller

  alias ChatApp.Chat

  def index(conn, %{"room_id" => room_id} = params) do
    opts =
      params
      |> Map.take(["before_id", "limit"])
      |> Enum.reduce([], fn
        {"before_id", v}, acc -> Keyword.put(acc, :before_id, String.to_integer(v))
        {"limit", v}, acc -> Keyword.put(acc, :limit, String.to_integer(v))
      end)

    messages = Chat.list_messages(String.to_integer(room_id), opts)
    render(conn, :index, messages: messages)
  end
end
