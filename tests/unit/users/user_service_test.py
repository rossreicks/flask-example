import uuid
from unittest.mock import MagicMock

import pytest

import app.users.user_oauth_account_model  # noqa: F401
from app.exceptions import UserNotFoundError
from app.users.user_model import User
from app.users.user_service import UserService


def _make_service(user_repo=None):
    return UserService(user_repo=user_repo or MagicMock())


def test_get_user_returns_user():
    user_repo = MagicMock()
    user_id = uuid.uuid4()
    expected = User(email="test@example.com", display_name="Test")
    expected.id = user_id
    user_repo.find_by_id.return_value = expected

    service = _make_service(user_repo=user_repo)
    result = service.get_user(user_id)

    assert result.email == "test@example.com"


def test_get_user_raises_when_not_found():
    user_repo = MagicMock()
    user_repo.find_by_id.return_value = None

    service = _make_service(user_repo=user_repo)
    with pytest.raises(UserNotFoundError):
        service.get_user(uuid.uuid4())


def test_get_me_returns_user():
    user_repo = MagicMock()
    user_id = uuid.uuid4()
    expected = User(email="me@example.com", display_name="Me")
    expected.id = user_id
    user_repo.find_by_id.return_value = expected

    service = _make_service(user_repo=user_repo)
    result = service.get_me(user_id)

    assert result.email == "me@example.com"
