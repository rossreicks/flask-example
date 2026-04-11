import uuid
from unittest.mock import MagicMock

import pytest

from app.exceptions import NotAMemberError, ThreadNotFoundError
from app.messages.message_model import Message
from app.messages.message_service import MessageService
from app.threads.thread_model import Thread


def _make_service(message_repo=None, thread_repo=None, session=None):
    return MessageService(
        message_repo=message_repo or MagicMock(),
        thread_repo=thread_repo or MagicMock(),
        session=session or MagicMock(),
    )


def test_send_message_raises_when_thread_not_found():
    thread_repo = MagicMock()
    thread_repo.find_by_id.return_value = None

    service = _make_service(thread_repo=thread_repo)
    with pytest.raises(ThreadNotFoundError):
        service.send_message(user_id=uuid.uuid4(), thread_id=uuid.uuid4(), content="hello")


def test_send_message_raises_when_not_a_member():
    thread_repo = MagicMock()
    thread_repo.find_by_id.return_value = Thread(name="general", created_by=uuid.uuid4())
    thread_repo.is_member.return_value = False

    service = _make_service(thread_repo=thread_repo)
    with pytest.raises(NotAMemberError):
        service.send_message(user_id=uuid.uuid4(), thread_id=uuid.uuid4(), content="hello")


def test_send_message_creates_and_returns_message():
    thread_repo = MagicMock()
    message_repo = MagicMock()
    session = MagicMock()
    user_id = uuid.uuid4()
    thread_id = uuid.uuid4()

    thread_repo.find_by_id.return_value = Thread(name="general", created_by=user_id)
    thread_repo.is_member.return_value = True

    expected_message = Message(thread_id=thread_id, user_id=user_id, content="hello")
    message_repo.create.return_value = expected_message

    service = _make_service(message_repo=message_repo, thread_repo=thread_repo, session=session)
    result = service.send_message(user_id=user_id, thread_id=thread_id, content="hello")

    assert result.content == "hello"
    message_repo.create.assert_called_once()
    session.commit.assert_called_once()


def test_list_messages_raises_when_thread_not_found():
    thread_repo = MagicMock()
    thread_repo.find_by_id.return_value = None

    service = _make_service(thread_repo=thread_repo)
    with pytest.raises(ThreadNotFoundError):
        service.list_messages(thread_id=uuid.uuid4())


def test_list_messages_returns_messages():
    thread_repo = MagicMock()
    message_repo = MagicMock()
    thread_id = uuid.uuid4()

    thread_repo.find_by_id.return_value = Thread(name="general", created_by=uuid.uuid4())
    expected = [MagicMock(), MagicMock()]
    message_repo.list_by_thread.return_value = expected

    service = _make_service(message_repo=message_repo, thread_repo=thread_repo)
    result = service.list_messages(thread_id=thread_id, limit=10)

    assert result == expected
    message_repo.list_by_thread.assert_called_once_with(thread_id, limit=10, offset=0)
