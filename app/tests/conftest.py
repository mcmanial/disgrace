import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost/chat_app_test"
)

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture(autouse=True)
async def clean_db():
    # SQLAlchemy's async engine pools raw asyncpg connections, which are not
    # safe to reuse across event loops. pytest-asyncio gives each test its
    # own loop by default, so drop any connections pooled under a previous
    # test's loop before this test touches the database.
    await engine.dispose()
    yield
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE messages, rooms, users RESTART IDENTITY CASCADE"))
