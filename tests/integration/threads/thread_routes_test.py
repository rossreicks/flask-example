import uuid

from app.users.user_model import User
from app.users.user_repository import UserRepository


def _create_authenticated_user(db_session, make_auth_header, email=None):
    repo = UserRepository(db_session)
    if email is None:
        email = f"threads-{uuid.uuid4()}@example.com"
    user = repo.create(User(email=email, display_name="Thread Tester"))
    db_session.commit()
    headers = make_auth_header(user.id)
    return user, headers


def test_create_thread(app, client, db_session, make_auth_header):
    user, headers = _create_authenticated_user(db_session, make_auth_header)

    response = client.post(
        "/threads",
        json={"name": "general"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "general"
    assert data["created_by"] == str(user.id)


def test_create_thread_requires_auth(client):
    response = client.post("/threads", json={"name": "general"})
    assert response.status_code == 401


def test_list_threads(app, client, db_session, make_auth_header):
    user, headers = _create_authenticated_user(db_session, make_auth_header)

    client.post("/threads", json={"name": "thread-1"}, headers=headers)
    client.post("/threads", json={"name": "thread-2"}, headers=headers)

    response = client.get("/threads", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2


def test_join_thread(app, client, db_session, make_auth_header):
    user1, headers1 = _create_authenticated_user(
        db_session, make_auth_header, f"creator-{uuid.uuid4()}@example.com"
    )
    user2, headers2 = _create_authenticated_user(
        db_session, make_auth_header, f"joiner-{uuid.uuid4()}@example.com"
    )

    create_resp = client.post("/threads", json={"name": "public"}, headers=headers1)
    thread_id = create_resp.get_json()["id"]

    join_resp = client.post(f"/threads/{thread_id}/join", headers=headers2)
    assert join_resp.status_code == 200
