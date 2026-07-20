from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import messages, rooms, sessions
from app.ws import router as ws_router

app = FastAPI(title="chat_app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, same_site="lax")

app.include_router(sessions.router)
app.include_router(rooms.router)
app.include_router(messages.router)
app.include_router(ws_router)
