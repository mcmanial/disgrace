defmodule ChatAppWeb.UserJSON do
  alias ChatApp.Chat.User

  def show(%{user: user}), do: data(user)

  def data(%User{} = user) do
    %{id: user.id, name: user.name}
  end
end
