defmodule ChatAppWeb.MessageJSON do
  alias ChatApp.Chat.Message

  def index(%{messages: messages}), do: %{data: for(message <- messages, do: data(message))}

  def data(%Message{} = message) do
    %{
      id: message.id,
      room_id: message.room_id,
      user_id: message.user_id,
      body: message.body,
      created_at: message.created_at
    }
  end
end
