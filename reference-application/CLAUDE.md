# Project: Chat App Backend

Backend-only API. Frontend is handled separately by another dev — do not build UI, templates, or htmx.

## Stack
- Language: Elixir / Phoenix
- DB: PostgreSQL, via Ecto
- Realtime: Phoenix Channels + Phoenix.PubSub (no manual broadcast plumbing)
- Auth: session-based (Plug.Session), not JWT — sessions are revocable and avoid token-in-localStorage exposure
- REST: standard Phoenix controllers for request/response endpoints
- WebSocket auth: authenticate at socket connect time (pull user_id from session/token passed in Socket init), not per-message

## Structure
```
lib/chat_app/
  application.ex
  repo.ex
  chat/
    room.ex          # schema
    message.ex       # schema
    user.ex          # schema
lib/chat_app_web/
  endpoint.ex
  router.ex
  channels/
    room_channel.ex  # join/1, handle_in for new_message, broadcast!/3
  controllers/
    room_controller.ex     # list/create rooms
    message_controller.ex  # paginated message history
```

## Schema (initial)
- `rooms(id, name)`
- `messages(id, room_id, user_id, body, created_at)`
- `users(id, name)`

## Conventions
- Message history loads via REST on channel join; live messages come through the channel after.
- Presence (`Phoenix.Presence`) is available if "who's online" is needed later — not implemented yet.
- Don't add features not explicitly requested (no read receipts, typing indicators, etc. unless asked).
- SQL: Postgres only, no other DB assumptions.
