defmodule ChatApp.Chat.User do
  use Ecto.Schema
  import Ecto.Changeset

  schema "users" do
    field :name, :string
  end

  def changeset(user, attrs) do
    user
    |> cast(attrs, [:name])
    |> validate_required([:name])
  end
end
