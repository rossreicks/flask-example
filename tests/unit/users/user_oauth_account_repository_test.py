from app.users.user_model import User
from app.users.user_oauth_account_model import UserOAuthAccount
from app.users.user_oauth_account_repository import UserOAuthAccountRepository
from app.users.user_repository import UserRepository


def _create_user(db_session, email="test@example.com"):
    repo = UserRepository(db_session)
    return repo.create(User(email=email, display_name="Test"))


def test_create_and_find_by_provider(db_session):
    user = _create_user(db_session)
    repo = UserOAuthAccountRepository(db_session)

    account = UserOAuthAccount(
        user_id=user.id,
        provider="google",
        provider_id="google-123",
    )
    repo.create(account)

    found = repo.find_by_provider("google", "google-123")
    assert found is not None
    assert found.user_id == user.id


def test_find_by_provider_returns_none_when_not_found(db_session):
    repo = UserOAuthAccountRepository(db_session)
    found = repo.find_by_provider("google", "nonexistent")
    assert found is None


def test_find_by_user_id(db_session):
    user = _create_user(db_session)
    repo = UserOAuthAccountRepository(db_session)

    repo.create(UserOAuthAccount(user_id=user.id, provider="google", provider_id="g-1"))
    repo.create(UserOAuthAccount(user_id=user.id, provider="github", provider_id="gh-1"))

    accounts = repo.find_by_user_id(user.id)
    assert len(accounts) == 2
    providers = {a.provider for a in accounts}
    assert providers == {"google", "github"}
