# Project: Chat App

Chat app (backend and frontend)

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

---

# Frontend: DaisyUI + Tailwind CSS

**Design system:** [Official DaisyUI Figma Library]
(reference ~/.claude/CLAUDE.md for file location)

## CRITICAL RULE
**Always use DaisyUI components and utility classes. Never invent custom component styles without explicit permission from the team.** If a DaisyUI component exists for a use case, use it — do not roll a bespoke alternative.

## Key DaisyUI components for this app

| Use case         | DaisyUI class(es)                                                  |
|------------------|--------------------------------------------------------------------|
| Chat messages    | `chat`, `chat-start`, `chat-end`, `chat-bubble`, `chat-header`, `chat-footer`, `chat-image` |
| Buttons          | `btn`, `btn-primary`, `btn-ghost`, `btn-sm`, `btn-circle`, etc.   |
| Text input       | `input`, `input-bordered`, `textarea`, `textarea-bordered`        |
| User avatars     | `avatar`, `avatar-online`, `avatar-offline`                       |
| Badges / status  | `badge`, `badge-primary`, `badge-ghost`                           |
| Navigation       | `navbar`, `menu`, `drawer`, `drawer-side`, `drawer-content`       |
| Layout           | `card`, `card-body`, `divider`, `hero`                            |
| Feedback         | `alert`, `alert-info`, `alert-success`, `alert-error`, `toast`   |
| Loading states   | `loading`, `loading-spinner`                                      |
| Modals           | `modal`, `modal-box`, `modal-action`                              |

## Theming
- Use DaisyUI semantic color tokens (`primary`, `secondary`, `accent`, `neutral`, `base-100`, etc.) — never hard-code hex values or raw Tailwind palette colors for component colors.
- Dark/light mode is handled via DaisyUI's `data-theme` attribute — do not implement a custom theme switcher unless asked.

## Do not
- Write custom CSS classes that duplicate DaisyUI component behavior.
- Use raw Tailwind classes to replicate a component that already exists in DaisyUI (e.g., don't build a button from `px-4 py-2 rounded bg-blue-500` when `btn btn-primary` exists).
- Override DaisyUI component styles inline without a clear reason tied to a specific product requirement.
