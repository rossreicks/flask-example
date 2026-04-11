from app.auth.auth_service import AuthService
from app.auth.oauth import FakeOAuthProvider, OAuthUserInfo
from app.users.user_oauth_account_repository import UserOAuthAccountRepository
from app.users.user_repository import UserRepository


def _make_fake_provider(
    email="oauth@example.com",
    display_name="OAuth User",
    provider="google",
    provider_id="g-123",
):
    return FakeOAuthProvider(
        OAuthUserInfo(
            email=email,
            display_name=display_name,
            avatar_url=None,
            provider=provider,
            provider_id=provider_id,
        )
    )


def _make_service(db_session, provider=None):
    return AuthService(
        provider=provider or _make_fake_provider(),
        user_repo=UserRepository(db_session),
        oauth_account_repo=UserOAuthAccountRepository(db_session),
        session=db_session,
        jwt_secret="test-secret",
    )


def test_login_creates_new_user_when_not_exists(db_session):
    service = _make_service(db_session)
    token, user = service.login(code="fake-code")

    assert token is not None
    assert user.email == "oauth@example.com"
    assert user.display_name == "OAuth User"


def test_login_returns_existing_user_when_email_matches(db_session):
    service = _make_service(db_session)
    _, user1 = service.login(code="fake-code")

    provider2 = _make_fake_provider(provider="github", provider_id="gh-456")
    service2 = _make_service(db_session, provider=provider2)
    _, user2 = service2.login(code="fake-code")

    assert user1.id == user2.id


def test_login_links_new_oauth_account_to_existing_user(db_session):
    service = _make_service(db_session)
    service.login(code="fake-code")

    provider2 = _make_fake_provider(provider="github", provider_id="gh-456")
    service2 = _make_service(db_session, provider=provider2)
    service2.login(code="fake-code")

    oauth_repo = UserOAuthAccountRepository(db_session)
    user_repo = UserRepository(db_session)
    user = user_repo.find_by_email("oauth@example.com")
    accounts = oauth_repo.find_by_user_id(user.id)
    assert len(accounts) == 2
    providers = {a.provider for a in accounts}
    assert providers == {"google", "github"}


def test_login_does_not_duplicate_oauth_account(db_session):
    service = _make_service(db_session)
    service.login(code="fake-code")
    service.login(code="fake-code")

    oauth_repo = UserOAuthAccountRepository(db_session)
    user_repo = UserRepository(db_session)
    user = user_repo.find_by_email("oauth@example.com")
    accounts = oauth_repo.find_by_user_id(user.id)
    assert len(accounts) == 1
