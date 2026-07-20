defmodule ChatApp.Chat do
  import Ecto.Query, warn: false

  alias ChatApp.Repo
  alias ChatApp.Chat.{Room, Message, User}

  def list_rooms do
    Repo.all(Room)
  end

  def get_room!(id), do: Repo.get!(Room, id)

  def create_room(attrs) do
    %Room{}
    |> Room.changeset(attrs)
    |> Repo.insert()
  end

  def get_user!(id), do: Repo.get!(User, id)

  def create_user(attrs) do
    %User{}
    |> User.changeset(attrs)
    |> Repo.insert()
  end

  def list_messages(room_id, opts \\ []) do
    limit = Keyword.get(opts, :limit, 50)
    before_id = Keyword.get(opts, :before_id)

    Message
    |> where([m], m.room_id == ^room_id)
    |> maybe_before(before_id)
    |> order_by([m], desc: m.id)
    |> limit(^limit)
    |> Repo.all()
    |> Enum.reverse()
  end

  defp maybe_before(query, nil), do: query
  defp maybe_before(query, before_id), do: where(query, [m], m.id < ^before_id)

  def create_message(attrs) do
    %Message{}
    |> Message.changeset(attrs)
    |> Repo.insert()
  end
end
