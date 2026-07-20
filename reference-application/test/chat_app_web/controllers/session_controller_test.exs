defmodule ChatAppWeb.SessionControllerTest do
  use ChatAppWeb.ConnCase, async: true

  test "POST /api/session creates a user and returns it", %{conn: conn} do
    conn = post(conn, ~p"/api/session", %{"name" => "mike"})
    assert %{"id" => id, "name" => "mike"} = json_response(conn, 201)
    assert is_integer(id)
    assert get_session(conn, :user_id) == id
  end

  test "DELETE /api/session clears the session", %{conn: conn} do
    conn = conn |> post(~p"/api/session", %{"name" => "mike"}) |> delete(~p"/api/session")
    assert response(conn, 204)

    conn = get(conn, ~p"/api/rooms")
    assert json_response(conn, 401)
  end
end
