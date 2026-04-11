import uuid

from app.users.user_model import User
from app.users.user_repository import UserRepository


def _setup_user_and_thread(client, db_session, make_auth_header):
    repo = UserRepository(db_session)
    user = repo.create(
        User(email=f"msg-route-{uuid.uuid4()}@example.com", display_name="Msg Tester")
    )
    db_session.commit()
    headers = make_auth_header(user.id)

    resp = client.post("/threads", json={"name": "chat"}, headers=headers)
    thread_id = resp.get_json()["id"]
    return user, headers, thread_id


def test_send_message(app, client, db_session, make_auth_header):
    user, headers, thread_id = _setup_user_and_thread(client, db_session, make_auth_header)

    response = client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "hello world"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["content"] == "hello world"
    assert data["user_id"] == str(user.id)


def test_send_message_requires_membership(app, client, db_session, make_auth_header):
    _, headers1, thread_id = _setup_user_and_thread(client, db_session, make_auth_header)

    repo = UserRepository(db_session)
    outsider = repo.create(
        User(email=f"outsider-{uuid.uuid4()}@example.com", display_name="Outsider")
    )
    db_session.commit()
    headers2 = make_auth_header(outsider.id)

    response = client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "should fail"},
        headers=headers2,
    )
    assert response.status_code == 403


def test_list_messages(app, client, db_session, make_auth_header):
    user, headers, thread_id = _setup_user_and_thread(client, db_session, make_auth_header)

    client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "msg 1"},
        headers=headers,
    )
    client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "msg 2"},
        headers=headers,
    )

    response = client.get(f"/threads/{thread_id}/messages", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["content"] == "msg 1"
