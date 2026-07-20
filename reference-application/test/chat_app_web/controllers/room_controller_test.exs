defmodule ChatAppWeb.RoomControllerTest do
  use ChatAppWeb.ConnCase, async: true

  defp log_in(conn, name \\ "mike") do
    post(conn, ~p"/api/session", %{"name" => name})
  end

  test "GET /api/rooms without a session is unauthenticated", %{conn: conn} do
    conn = get(conn, ~p"/api/rooms")
    assert json_response(conn, 401) == %{"error" => "unauthenticated"}
  end

  test "POST /api/rooms creates a room when authenticated", %{conn: conn} do
    conn = conn |> log_in() |> post(~p"/api/rooms", %{"name" => "general"})
    assert %{"id" => id, "name" => "general"} = json_response(conn, 201)
    assert is_integer(id)
  end

  test "GET /api/rooms lists rooms when authenticated", %{conn: conn} do
    conn = conn |> log_in()
    conn = post(conn, ~p"/api/rooms", %{"name" => "general"})
    conn = get(conn, ~p"/api/rooms")
    assert [%{"name" => "general"}] = json_response(conn, 200)["data"]
  end
end
