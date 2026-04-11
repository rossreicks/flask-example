import uuid

from app.threads.thread_model import Thread
from app.threads.thread_repository import ThreadRepository
from app.users.user_model import User
from app.users.user_repository import UserRepository


def _create_user(db_session, email="thread-test@example.com"):
    repo = UserRepository(db_session)
    return repo.create(User(email=email, display_name="Test"))


def test_create_and_find_by_id(db_session):
    user = _create_user(db_session)
    repo = ThreadRepository(db_session)

    thread = Thread(name="general", created_by=user.id)
    created = repo.create(thread)

    assert created.id is not None
    found = repo.find_by_id(created.id)
    assert found is not None
    assert found.name == "general"


def test_find_by_id_returns_none_when_not_found(db_session):
    repo = ThreadRepository(db_session)
    found = repo.find_by_id(uuid.uuid4())
    assert found is None


def test_add_member_and_is_member(db_session):
    user = _create_user(db_session)
    repo = ThreadRepository(db_session)

    thread = repo.create(Thread(name="general", created_by=user.id))
    repo.add_member(thread.id, user.id)

    assert repo.is_member(thread.id, user.id) is True


def test_is_member_returns_false_when_not_member(db_session):
    user = _create_user(db_session)
    repo = ThreadRepository(db_session)

    thread = repo.create(Thread(name="general", created_by=user.id))
    assert repo.is_member(thread.id, uuid.uuid4()) is False


def test_list_members(db_session):
    user1 = _create_user(db_session, "u1@example.com")
    user2 = _create_user(db_session, "u2@example.com")
    repo = ThreadRepository(db_session)

    thread = repo.create(Thread(name="general", created_by=user1.id))
    repo.add_member(thread.id, user1.id)
    repo.add_member(thread.id, user2.id)

    members = repo.list_members(thread.id)
    assert len(members) == 2


def test_list_threads_for_user(db_session):
    user = _create_user(db_session)
    repo = ThreadRepository(db_session)

    t1 = repo.create(Thread(name="thread-1", created_by=user.id))
    t2 = repo.create(Thread(name="thread-2", created_by=user.id))
    repo.add_member(t1.id, user.id)
    repo.add_member(t2.id, user.id)

    threads = repo.list_for_user(user.id)
    assert len(threads) == 2
    names = {t.name for t in threads}
    assert names == {"thread-1", "thread-2"}
