defmodule ChatAppWeb.ChannelCase do
  use ExUnit.CaseTemplate

  using do
    quote do
      import Phoenix.ChannelTest
      import ChatAppWeb.ChannelCase

      @endpoint ChatAppWeb.Endpoint
    end
  end

  setup tags do
    ChatApp.DataCase.setup_sandbox(tags)
    :ok
  end
end
