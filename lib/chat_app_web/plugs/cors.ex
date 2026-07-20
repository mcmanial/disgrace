defmodule ChatAppWeb.Plugs.Cors do
  @moduledoc """
  Permits cross-origin requests from any localhost/127.0.0.1 origin, with
  credentials, so a separately-served frontend (dev tools, the real
  frontend's dev server) can use the session cookie during local
  development. Origins that don't match are left untouched, so this is a
  no-op against real production origins.
  """

  import Plug.Conn

  @origin_regex ~r{\Ahttps?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?\z}

  def init(opts), do: opts

  def call(conn, _opts) do
    case get_req_header(conn, "origin") do
      [origin] when origin != "" ->
        if Regex.match?(@origin_regex, origin) do
          conn
          |> put_resp_header("access-control-allow-origin", origin)
          |> put_resp_header("access-control-allow-credentials", "true")
          |> put_resp_header("vary", "origin")
          |> handle_preflight()
        else
          conn
        end

      _ ->
        conn
    end
  end

  defp handle_preflight(%{method: "OPTIONS"} = conn) do
    conn
    |> put_resp_header("access-control-allow-methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
    |> put_resp_header("access-control-allow-headers", "content-type")
    |> put_resp_header("access-control-max-age", "86400")
    |> send_resp(:no_content, "")
    |> halt()
  end

  defp handle_preflight(conn), do: conn
end
