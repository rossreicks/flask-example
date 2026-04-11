from typing import cast

from flask import current_app
from sqlalchemy.orm import Session

from app.auth.auth_service import AuthService
from app.auth.oauth import GitHubOAuthProvider, GoogleOAuthProvider, OAuthProvider
from app.extensions import db
from app.messages.message_repository import MessageRepository
from app.messages.message_service import MessageService
from app.threads.thread_repository import ThreadRepository
from app.threads.thread_service import ThreadService
from app.users.user_oauth_account_repository import UserOAuthAccountRepository
from app.users.user_repository import UserRepository
from app.users.user_service import UserService


def get_user_service(session=None) -> UserService:
    session = cast(Session, session or db.session)
    return UserService(user_repo=UserRepository(session))


def get_thread_service(session=None) -> ThreadService:
    session = cast(Session, session or db.session)
    return ThreadService(
        thread_repo=ThreadRepository(session),
        session=session,
    )


def get_message_service(session=None) -> MessageService:
    session = cast(Session, session or db.session)
    return MessageService(
        message_repo=MessageRepository(session),
        thread_repo=ThreadRepository(session),
        session=session,
    )


def get_oauth_provider(provider_name: str) -> OAuthProvider:
    config = current_app.config
    if provider_name == "google":
        return GoogleOAuthProvider(
            client_id=config["GOOGLE_CLIENT_ID"],
            client_secret=config["GOOGLE_CLIENT_SECRET"],
            redirect_uri=config["GOOGLE_REDIRECT_URI"],
        )
    elif provider_name == "github":
        return GitHubOAuthProvider(
            client_id=config["GITHUB_CLIENT_ID"],
            client_secret=config["GITHUB_CLIENT_SECRET"],
            redirect_uri=config["GITHUB_REDIRECT_URI"],
        )
    raise ValueError(f"Unknown OAuth provider: {provider_name}")


def get_auth_service(provider: OAuthProvider, session=None) -> AuthService:
    session = cast(Session, session or db.session)
    return AuthService(
        provider=provider,
        user_repo=UserRepository(session),
        oauth_account_repo=UserOAuthAccountRepository(session),
        session=session,
        jwt_secret=current_app.config["JWT_SECRET"],
    )
