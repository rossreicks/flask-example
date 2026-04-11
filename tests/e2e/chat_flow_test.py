"""
End-to-end test: full chat flow through REST and WebSocket.

1. Two users authenticate via OAuth
2. User 1 creates a thread
3. User 2 joins the thread
4. User 1 sends a message via WebSocket
5. User 2 receives the message via WebSocket
6. Messages are retrievable via REST
"""

from app.auth.oauth import FakeOAuthProvider, OAuthUserInfo
from app.extensions import socketio


def _login_user(app, client, email, display_name, provider_id):
    fake = FakeOAuthProvider(
        OAuthUserInfo(
            email=email,
            display_name=display_name,
            avatar_url=None,
            provider="google",
            provider_id=provider_id,
        )
    )
    app.config["_test_oauth_provider"] = fake
    response = client.get("/auth/google/callback?code=fake&state=test")
    data = response.get_json()
    return data["token"], data["user"]


def test_full_chat_flow(app, client):
    # Step 1: Two users authenticate
    token1, user1 = _login_user(app, client, "alice@example.com", "Alice", "g-alice")
    token2, _ = _login_user(app, client, "bob@example.com", "Bob", "g-bob")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Step 2: Alice creates a thread
    create_resp = client.post("/threads", json={"name": "project-chat"}, headers=headers1)
    assert create_resp.status_code == 201
    thread_id = create_resp.get_json()["id"]

    # Step 3: Bob joins the thread
    join_resp = client.post(f"/threads/{thread_id}/join", headers=headers2)
    assert join_resp.status_code == 200

    # Step 4: Both connect via WebSocket and join the thread room
    ws1 = socketio.test_client(app, headers=headers1)
    ws2 = socketio.test_client(app, headers=headers2)

    assert ws1.is_connected()
    assert ws2.is_connected()

    ws1.emit("join_thread", {"thread_id": thread_id})
    ws2.emit("join_thread", {"thread_id": thread_id})
    ws1.get_received()  # clear
    ws2.get_received()  # clear

    # Step 5: Alice sends a message, Bob receives it
    ws1.emit("send_message", {"thread_id": thread_id, "content": "Hey Bob!"})

    bob_received = ws2.get_received()
    new_messages = [m for m in bob_received if m["name"] == "new_message"]
    assert len(new_messages) == 1
    assert new_messages[0]["args"][0]["content"] == "Hey Bob!"
    assert new_messages[0]["args"][0]["user_id"] == user1["id"]

    # Step 6: Messages retrievable via REST
    list_resp = client.get(f"/threads/{thread_id}/messages", headers=headers2)
    assert list_resp.status_code == 200
    messages = list_resp.get_json()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hey Bob!"

    ws1.disconnect()
    ws2.disconnect()
