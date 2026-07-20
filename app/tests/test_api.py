async def login(client, name="mike"):
    resp = await client.post("/api/session", json={"name": name})
    assert resp.status_code == 201
    return resp.json()


async def test_create_session(client):
    user = await login(client)
    assert user["name"] == "mike"
    assert isinstance(user["id"], int)


async def test_rooms_require_auth(client):
    resp = await client.get("/api/rooms")
    assert resp.status_code == 401


async def test_create_and_list_rooms(client):
    await login(client)

    resp = await client.post("/api/rooms", json={"name": "general"})
    assert resp.status_code == 201
    assert resp.json()["name"] == "general"

    resp = await client.get("/api/rooms")
    assert resp.status_code == 200
    assert [r["name"] for r in resp.json()] == ["general"]


async def test_delete_session_revokes_access(client):
    await login(client)
    resp = await client.delete("/api/session")
    assert resp.status_code == 204

    resp = await client.get("/api/rooms")
    assert resp.status_code == 401


async def test_message_history_empty(client):
    await login(client)
    room = (await client.post("/api/rooms", json={"name": "general"})).json()

    resp = await client.get(f"/api/rooms/{room['id']}/messages")
    assert resp.status_code == 200
    assert resp.json() == []
