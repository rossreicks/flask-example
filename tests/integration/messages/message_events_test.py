import uuid

from app.extensions import socketio
from app.threads.thread_model import Thread
from app.threads.thread_repository import ThreadRepository
from app.users.user_model import User
from app.users.user_repository import UserRepository


def _setup(db_session):
    user_repo = UserRepository(db_session)
    thread_repo = ThreadRepository(db_session)

    user = user_repo.create(User(email=f"ws-{uuid.uuid4()}@example.com", display_name="WS Tester"))
    thread = thread_repo.create(Thread(name="ws-thread", created_by=user.id))
    thread_repo.add_member(thread.id, user.id)
    db_session.commit()
    return user, thread


def test_join_thread_event(app, db_session, make_auth_header):
    user, thread = _setup(db_session)
    headers = make_auth_header(user.id)

    ws_client = socketio.test_client(app, headers=headers)
    assert ws_client.is_connected()

    ws_client.emit("join_thread", {"thread_id": str(thread.id)})
    received = ws_client.get_received()

    assert any(msg["name"] == "thread_joined" for msg in received)
    ws_client.disconnect()


def test_send_message_event_broadcasts(app, db_session, make_auth_header):
    user, thread = _setup(db_session)
    headers = make_auth_header(user.id)

    ws_client = socketio.test_client(app, headers=headers)
    ws_client.emit("join_thread", {"thread_id": str(thread.id)})
    ws_client.get_received()  # clear join messages

    ws_client.emit(
        "send_message",
        {
            "thread_id": str(thread.id),
            "content": "hello via websocket",
        },
    )
    received = ws_client.get_received()

    new_message_events = [m for m in received if m["name"] == "new_message"]
    assert len(new_message_events) == 1
    assert new_message_events[0]["args"][0]["content"] == "hello via websocket"
    ws_client.disconnect()


def test_send_message_event_rejected_without_auth(app):
    ws_client = socketio.test_client(app)
    assert not ws_client.is_connected()
