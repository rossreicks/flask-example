import uuid
from unittest.mock import MagicMock

import pytest

from app.exceptions import ThreadNotFoundError
from app.threads.thread_model import Thread
from app.threads.thread_service import ThreadService


def _make_service(thread_repo=None, session=None):
    return ThreadService(
        thread_repo=thread_repo or MagicMock(),
        session=session or MagicMock(),
    )


def test_create_thread_adds_creator_as_member():
    thread_repo = MagicMock()
    thread_id = uuid.uuid4()
    user_id = uuid.uuid4()

    created_thread = Thread(name="general", created_by=user_id)
    created_thread.id = thread_id
    thread_repo.create.return_value = created_thread

    service = _make_service(thread_repo=thread_repo)
    result = service.create_thread(name="general", user_id=user_id)

    assert result.name == "general"
    thread_repo.add_member.assert_called_once_with(thread_id, user_id)


def test_join_thread_raises_when_thread_not_found():
    thread_repo = MagicMock()
    thread_repo.find_by_id.return_value = None

    service = _make_service(thread_repo=thread_repo)
    with pytest.raises(ThreadNotFoundError):
        service.join_thread(thread_id=uuid.uuid4(), user_id=uuid.uuid4())


def test_join_thread_adds_member():
    thread_repo = MagicMock()
    thread_id = uuid.uuid4()
    user_id = uuid.uuid4()
    thread_repo.find_by_id.return_value = Thread(name="general", created_by=uuid.uuid4())
    thread_repo.is_member.return_value = False

    service = _make_service(thread_repo=thread_repo)
    service.join_thread(thread_id=thread_id, user_id=user_id)

    thread_repo.add_member.assert_called_once_with(thread_id, user_id)


def test_list_threads_for_user():
    thread_repo = MagicMock()
    user_id = uuid.uuid4()
    expected = [Thread(name="t1", created_by=user_id)]
    thread_repo.list_for_user.return_value = expected

    service = _make_service(thread_repo=thread_repo)
    result = service.list_threads(user_id=user_id)

    assert result == expected
    thread_repo.list_for_user.assert_called_once_with(user_id)
