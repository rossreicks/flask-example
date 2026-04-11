import uuid

from app.users.user_model import User
from app.users.user_repository import UserRepository


def test_create_and_find_by_id(db_session):
    repo = UserRepository(db_session)
    user = User(
        email="test@example.com",
        display_name="Test User",
    )
    created = repo.create(user)

    assert created.id is not None
    found = repo.find_by_id(created.id)
    assert found is not None
    assert found.email == "test@example.com"


def test_find_by_id_returns_none_when_not_found(db_session):
    repo = UserRepository(db_session)
    found = repo.find_by_id(uuid.uuid4())
    assert found is None


def test_find_by_email(db_session):
    repo = UserRepository(db_session)
    user = User(email="find@example.com", display_name="Find Me")
    repo.create(user)

    found = repo.find_by_email("find@example.com")
    assert found is not None
    assert found.display_name == "Find Me"


def test_find_by_email_returns_none_when_not_found(db_session):
    repo = UserRepository(db_session)
    found = repo.find_by_email("nonexistent@example.com")
    assert found is None
