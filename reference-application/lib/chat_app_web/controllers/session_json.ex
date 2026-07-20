defmodule ChatAppWeb.SessionJSON do
  alias ChatAppWeb.UserJSON

  def show(%{user: user}), do: UserJSON.data(user)
end
