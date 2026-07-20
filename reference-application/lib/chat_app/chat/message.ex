defmodule ChatApp.Chat.Message do
  use Ecto.Schema
  import Ecto.Changeset

  alias ChatApp.Chat.{Room, User}

  schema "messages" do
    field :body, :string

    belongs_to :room, Room
    belongs_to :user, User

    timestamps(inserted_at: :created_at, updated_at: false)
  end

  def changeset(message, attrs) do
    message
    |> cast(attrs, [:body, :room_id, :user_id])
    |> validate_required([:body, :room_id, :user_id])
    |> foreign_key_constraint(:room_id)
    |> foreign_key_constraint(:user_id)
  end
end
