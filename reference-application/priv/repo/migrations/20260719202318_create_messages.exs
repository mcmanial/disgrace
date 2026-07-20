defmodule ChatApp.Repo.Migrations.CreateMessages do
  use Ecto.Migration

  def change do
    create table(:messages) do
      add :room_id, references(:rooms, on_delete: :delete_all), null: false
      add :user_id, references(:users, on_delete: :delete_all), null: false
      add :body, :text, null: false

      timestamps(inserted_at: :created_at, updated_at: false)
    end

    create index(:messages, [:room_id])
    create index(:messages, [:user_id])
  end
end
