import uuid

from app.messages.message_model import Message
from app.messages.message_repository import MessageRepository
from app.threads.thread_model import Thread
from app.threads.thread_repository import ThreadRepository
from app.users.user_model import User
from app.users.user_repository import UserRepository


def _setup(db_session):
    user = UserRepository(db_session).create(
        User(email="msg-test@example.com", display_name="Test")
    )
    thread = ThreadRepository(db_session).create(Thread(name="general", created_by=user.id))
    return user, thread


def test_create_and_find_by_id(db_session):
    user, thread = _setup(db_session)
    repo = MessageRepository(db_session)

    message = Message(thread_id=thread.id, user_id=user.id, content="hello")
    created = repo.create(message)

    assert created.id is not None
    found = repo.find_by_id(created.id)
    assert found is not None
    assert found.content == "hello"


def test_find_by_id_returns_none_when_not_found(db_session):
    repo = MessageRepository(db_session)
    found = repo.find_by_id(uuid.uuid4())
    assert found is None


def test_list_by_thread_returns_messages_in_order(db_session):
    user, thread = _setup(db_session)
    repo = MessageRepository(db_session)

    repo.create(Message(thread_id=thread.id, user_id=user.id, content="first"))
    repo.create(Message(thread_id=thread.id, user_id=user.id, content="second"))
    repo.create(Message(thread_id=thread.id, user_id=user.id, content="third"))

    messages = repo.list_by_thread(thread.id)
    assert len(messages) == 3
    assert messages[0].content == "first"
    assert messages[2].content == "third"


def test_list_by_thread_with_limit(db_session):
    user, thread = _setup(db_session)
    repo = MessageRepository(db_session)

    for i in range(5):
        repo.create(Message(thread_id=thread.id, user_id=user.id, content=f"msg-{i}"))

    messages = repo.list_by_thread(thread.id, limit=3)
    assert len(messages) == 3
