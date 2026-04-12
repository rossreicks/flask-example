# React Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a React + Vite frontend using Inertia.js, migrate auth from JWT to Flask-Login sessions, and establish a page/layout component convention with Tailwind + shadcn.

**Architecture:** Flask serves all routes — both REST API (`/api/...`) and Inertia page routes (`/threads`, `/auth/login`, etc.). The Inertia protocol connects Flask route handlers to React page components via props. WebSocket (Flask-SocketIO) is unchanged server-side; clients connect from within `.page.tsx` components. Vite builds to `app/static/dist/` which Flask serves in production; in dev, Flask renders `spa_root.html` referencing the Vite dev server for HMR.

**Tech Stack:** Python — flask-login, flask-inertia; Frontend — React 18, TypeScript, Vite 6, Inertia.js v2, Tailwind CSS v4, shadcn/ui, socket.io-client, pnpm

---

## File Map

**Modified:**
- `pyproject.toml` — add flask-login, flask-inertia; remove pyjwt
- `app/extensions.py` — add LoginManager, Inertia
- `app/__init__.py` — init login_manager/inertia, user_loader, vite context processor, register spa_bp last
- `app/config.py` — remove JWT_SECRET
- `app/auth/auth_service.py` — remove jwt_secret param, `login()` returns `User` not `tuple[str, User]`
- `app/auth/decorators.py` — use `current_user` from Flask-Login instead of JWT header parsing
- `app/auth/auth_routes.py` — add `/auth/login` Inertia page, callback calls `login_user()`, add `/auth/logout`
- `app/threads/thread_routes.py` — REST routes move to `/api/threads`, add Inertia page routes at `/threads`
- `app/messages/message_routes.py` — REST routes move to `/api/threads/<id>/messages`
- `app/messages/message_events.py` — remove JWT, use `current_user`
- `app/users/user_routes.py` — url_prefix changes to `/api/users`
- `app/users/user_model.py` — add UserMixin
- `app/dependencies.py` — remove jwt_secret from get_auth_service
- `tests/conftest.py` — remove JWT helpers, add `login_as()`
- `tests/unit/auth/auth_service_test.py` — no jwt_secret, login() returns User
- `tests/integration/auth/auth_routes_test.py` — session-based assertions
- `tests/integration/threads/thread_routes_test.py` — session auth + `/api/threads` URLs
- `tests/integration/messages/message_routes_test.py` — session auth + `/api/threads/<id>/messages` URLs
- `tests/integration/messages/message_events_test.py` — session-based WS auth
- `tests/integration/users/user_routes_test.py` — session auth + `/api/users/me`
- `tests/e2e/chat_flow_test.py` — session auth, two clients, new URLs
- `Makefile` — add frontend targets, split dev into run + frontend-dev
- `lefthook.yml` — add frontend-lint and frontend-typecheck
- `Dockerfile` — add Node build stage
- `docker-compose.yml` — remove JWT_SECRET
- `.gitignore` — add app/static/dist/, frontend/node_modules/

**Deleted:**
- `app/auth/jwt.py`

**Created:**
- `app/spa/__init__.py`
- `app/spa/spa_routes.py`
- `app/templates/spa_root.html`
- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tsconfig.json`
- `frontend/index.html`
- `frontend/components.json`
- `frontend/src/main.tsx`
- `frontend/src/index.css`
- `frontend/src/lib/utils.ts`
- `frontend/src/components/button.tsx`
- `frontend/src/pages/auth/Login.page.tsx`
- `frontend/src/pages/auth/Login.layout.tsx`
- `frontend/src/pages/home/Home.page.tsx`
- `frontend/src/pages/home/Home.layout.tsx`
- `frontend/src/pages/threads/ThreadList.page.tsx`
- `frontend/src/pages/threads/ThreadList.layout.tsx`
- `frontend/src/pages/threads/ThreadDetail.page.tsx`
- `frontend/src/pages/threads/ThreadDetail.layout.tsx`
- `frontend/src/hooks/useSocket.ts`
- `frontend/src/hooks/useLocalStorage.ts`

---

## Task 1: Add flask-login and flask-inertia, remove pyjwt

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update pyproject.toml**

Replace the dependencies section:

```toml
[project]
name = "flask-example"
version = "0.1.0"
description = "A testable Flask chat application demonstrating clean architecture"
requires-python = ">=3.12"
dependencies = [
    "flask>=3.1",
    "flask-socketio>=5.4",
    "flask-sqlalchemy>=3.1",
    "flask-migrate>=4.0",
    "flask-login>=0.6",
    "flask-inertia>=0.5",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "requests>=2.32",
    "python-dotenv>=1.0",
    "gunicorn>=23.0",
    "eventlet>=0.37",
]
```

- [ ] **Step 2: Sync dependencies**

```bash
uv sync
```

Expected: resolves flask-login and flask-inertia, removes pyjwt from the lockfile.

- [ ] **Step 3: Verify existing tests still pass**

```bash
uv run pytest tests/unit -q
```

Expected: all unit tests pass (pyjwt still present in venv until fully removed from imports).

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add flask-login and flask-inertia, remove pyjwt"
```

---

## Task 2: Wire Flask-Login and Inertia into app infrastructure

**Files:**
- Modify: `app/extensions.py`
- Modify: `app/users/user_model.py`

- [ ] **Step 1: Update extensions.py**

```python
from flask_inertia import Inertia
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()
login_manager = LoginManager()
inertia = Inertia()
```

- [ ] **Step 2: Add UserMixin to User model**

In `app/users/user_model.py`, add the import and mixin:

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from flask_login import UserMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.users.user_oauth_account_model import UserOAuthAccount


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    oauth_accounts: Mapped[list["UserOAuthAccount"]] = relationship(  # noqa: UP037
        "UserOAuthAccount", back_populates="user"
    )

    def get_id(self) -> str:
        return str(self.id)
```

- [ ] **Step 3: Verify existing tests still pass**

```bash
uv run pytest tests/unit -q
```

Expected: all unit tests pass (LoginManager/Inertia added but not yet wired into create_app).

- [ ] **Step 4: Commit**

```bash
git add app/extensions.py app/users/user_model.py
git commit -m "feat: add LoginManager and Inertia extensions, UserMixin on User"
```

---

## Task 3: Remove JWT — migrate AuthService, decorators, WebSocket events

This task removes all JWT code atomically. Write the updated tests first to define the new expected behavior, then update the implementation to make them pass.

**Files:**
- Delete: `app/auth/jwt.py`
- Modify: `app/auth/auth_service.py`
- Modify: `app/auth/decorators.py`
- Modify: `app/messages/message_events.py`
- Modify: `app/dependencies.py`
- Modify: `app/config.py`
- Modify: `tests/conftest.py`
- Modify: `tests/unit/auth/auth_service_test.py`

- [ ] **Step 1: Write updated auth_service_test.py (login returns User, no jwt_secret)**

Replace `tests/unit/auth/auth_service_test.py`:

```python
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
    )


def test_login_creates_new_user_when_not_exists(db_session):
    service = _make_service(db_session)
    user = service.login(code="fake-code")

    assert user is not None
    assert user.email == "oauth@example.com"
    assert user.display_name == "OAuth User"


def test_login_returns_existing_user_when_email_matches(db_session):
    service = _make_service(db_session)
    user1 = service.login(code="fake-code")

    provider2 = _make_fake_provider(provider="github", provider_id="gh-456")
    service2 = _make_service(db_session, provider=provider2)
    user2 = service2.login(code="fake-code")

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
    assert user is not None
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
    assert user is not None
    accounts = oauth_repo.find_by_user_id(user.id)
    assert len(accounts) == 1
```

- [ ] **Step 2: Run auth_service tests — expect failure**

```bash
uv run pytest tests/unit/auth/auth_service_test.py -v
```

Expected: FAIL — `_make_service` passes no `jwt_secret` but `AuthService.__init__` requires it; `login()` returns `tuple[str, User]` but tests unpack as `User`.

- [ ] **Step 3: Update auth_service.py — remove JWT, return User**

Replace `app/auth/auth_service.py`:

```python
from sqlalchemy.orm import Session

from app.auth.oauth import OAuthProvider
from app.exceptions import UserNotFoundError
from app.users.user_model import User
from app.users.user_oauth_account_model import UserOAuthAccount
from app.users.user_oauth_account_repository import UserOAuthAccountRepository
from app.users.user_repository import UserRepository


class AuthService:
    def __init__(
        self,
        provider: OAuthProvider,
        user_repo: UserRepository,
        oauth_account_repo: UserOAuthAccountRepository,
        session: Session,
    ):
        self.provider = provider
        self.user_repo = user_repo
        self.oauth_account_repo = oauth_account_repo
        self.session = session

    def login(self, code: str) -> User:
        user_info = self.provider.exchange_code(code)

        existing_account = self.oauth_account_repo.find_by_provider(
            user_info.provider, user_info.provider_id
        )
        if existing_account:
            user = self.user_repo.find_by_id(existing_account.user_id)
            if user is None:
                raise UserNotFoundError(existing_account.user_id)
            return user

        user = self.user_repo.find_by_email(user_info.email)
        if not user:
            user = self.user_repo.create(
                User(
                    email=user_info.email,
                    display_name=user_info.display_name,
                    avatar_url=user_info.avatar_url,
                )
            )

        self.oauth_account_repo.create(
            UserOAuthAccount(
                user_id=user.id,
                provider=user_info.provider,
                provider_id=user_info.provider_id,
            )
        )

        self.session.flush()
        return user
```

- [ ] **Step 4: Update dependencies.py — remove jwt_secret**

Replace `app/dependencies.py`:

```python
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
    )
```

- [ ] **Step 5: Update config.py — remove JWT_SECRET**

Replace `app/config.py`:

```python
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/chat")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "")
    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI = os.environ.get("GITHUB_REDIRECT_URI", "")


class DevConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"


class ProdConfig(Config):
    DEBUG = False
```

- [ ] **Step 6: Rewrite decorators.py — use current_user**

Replace `app/auth/decorators.py`:

```python
import functools
import uuid

from flask_login import current_user
from flask_socketio import disconnect


def require_auth(f):
    """Protect REST API routes — returns 401 if the user is not authenticated."""

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)

    return decorated


def current_user_id() -> uuid.UUID:
    return current_user.id  # type: ignore[return-value]


def require_socket_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
            return
        return f(*args, **kwargs)

    return decorated
```

- [ ] **Step 7: Rewrite message_events.py — use current_user**

Replace `app/messages/message_events.py`:

```python
import uuid

from flask_login import current_user
from flask_socketio import emit, join_room

from app.dependencies import get_message_service
from app.exceptions import NotAMemberError, ThreadNotFoundError
from app.extensions import socketio


@socketio.on("connect")
def handle_connect(_auth=None):
    if not current_user.is_authenticated:
        return False


@socketio.on("disconnect")
def handle_disconnect():
    pass


@socketio.on("join_thread")
def handle_join_thread(data):
    thread_id = data["thread_id"]
    join_room(thread_id)
    emit("thread_joined", {"thread_id": thread_id})


@socketio.on("send_message")
def handle_send_message(data):
    if not current_user.is_authenticated:
        emit("error", {"message": "Unauthorized"})
        return

    service = get_message_service()
    try:
        message = service.send_message(
            user_id=current_user.id,
            thread_id=uuid.UUID(data["thread_id"]),
            content=data["content"],
        )
    except (ThreadNotFoundError, NotAMemberError) as e:
        emit("error", {"message": str(e)})
        return

    emit(
        "new_message",
        {
            "id": str(message.id),
            "thread_id": str(message.thread_id),
            "user_id": str(message.user_id),
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        },
        to=data["thread_id"],
    )
```

- [ ] **Step 8: Delete jwt.py**

```bash
rm app/auth/jwt.py
```

- [ ] **Step 9: Update conftest.py — remove JWT helpers, add login_as**

Replace `tests/conftest.py`:

```python
import uuid

import pytest
from testcontainers.postgres import PostgresContainer

from app import create_app
from app.config import TestConfig
from app.extensions import db as _db


@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16", driver="psycopg2") as pg:
        yield pg


@pytest.fixture(scope="session")
def app(postgres):
    TestConfig.SQLALCHEMY_DATABASE_URI = postgres.get_connection_url()
    application = create_app(config=TestConfig)

    with application.app_context():
        _db.create_all()

    yield application

    with application.app_context():
        _db.drop_all()


@pytest.fixture
def db_session(app):
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        session = _db.session
        session.bind = connection

        yield session

        transaction.rollback()
        connection.close()
        session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    from app.extensions import socketio

    return socketio.test_client(app)


def login_as(client, user_id: uuid.UUID) -> None:
    """Authenticate the test client as the given user via Flask-Login session."""
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True
```

- [ ] **Step 10: Run auth_service tests — expect pass**

```bash
uv run pytest tests/unit/auth/auth_service_test.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 11: Commit**

```bash
git add app/auth/auth_service.py app/auth/decorators.py app/auth/jwt.py \
        app/messages/message_events.py app/dependencies.py app/config.py \
        tests/conftest.py tests/unit/auth/auth_service_test.py
git commit -m "feat: replace JWT auth with Flask-Login sessions"
```

---

## Task 4: Rewrite auth routes + update auth route tests

**Files:**
- Modify: `app/auth/auth_routes.py`
- Modify: `tests/integration/auth/auth_routes_test.py`

- [ ] **Step 1: Write updated auth route tests**

Replace `tests/integration/auth/auth_routes_test.py`:

```python
from app.auth.oauth import FakeOAuthProvider, OAuthUserInfo
from app.users.user_repository import UserRepository


def _make_fake_provider(email, display_name, provider_id):
    return FakeOAuthProvider(
        OAuthUserInfo(
            email=email,
            display_name=display_name,
            avatar_url=None,
            provider="google",
            provider_id=provider_id,
        )
    )


def test_oauth_callback_creates_user_and_redirects(app, client, db_session):
    app.config["_test_oauth_provider"] = _make_fake_provider(
        "new@example.com", "New User", "g-999"
    )

    response = client.get(
        "/auth/google/callback?code=fake-code&state=test", follow_redirects=False
    )
    assert response.status_code == 302

    repo = UserRepository(db_session)
    user = repo.find_by_email("new@example.com")
    assert user is not None


def test_oauth_callback_logs_user_into_session(app, client):
    app.config["_test_oauth_provider"] = _make_fake_provider(
        "session@example.com", "Session User", "g-777"
    )

    client.get("/auth/google/callback?code=fake-code&state=test")
    with client.session_transaction() as sess:
        assert "_user_id" in sess


def test_oauth_callback_returns_same_user_on_second_login(app, client):
    app.config["_test_oauth_provider"] = _make_fake_provider(
        "returning@example.com", "Returning User", "g-888"
    )

    client.get("/auth/google/callback?code=fake-code&state=test")
    with client.session_transaction() as sess:
        user_id_1 = sess["_user_id"]

    client.get("/auth/google/callback?code=fake-code&state=test")
    with client.session_transaction() as sess:
        user_id_2 = sess["_user_id"]

    assert user_id_1 == user_id_2


def test_oauth_login_redirects(app, client):
    response = client.get("/auth/google/login")
    assert response.status_code == 302


def test_logout_clears_session(app, client):
    app.config["_test_oauth_provider"] = _make_fake_provider(
        "logout@example.com", "Logout User", "g-666"
    )
    client.get("/auth/google/callback?code=fake-code&state=test")

    with client.session_transaction() as sess:
        assert "_user_id" in sess

    client.get("/auth/logout")
    with client.session_transaction() as sess:
        assert "_user_id" not in sess
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/integration/auth/auth_routes_test.py -v
```

Expected: FAIL — callback returns 200 JSON (old behavior), no logout route exists.

- [ ] **Step 3: Rewrite auth_routes.py**

Replace `app/auth/auth_routes.py`:

```python
import secrets

from flask import Blueprint, current_app, redirect, url_for
from flask_inertia import render_inertia
from flask_login import current_user, login_required, login_user, logout_user

from app.dependencies import get_auth_service, get_oauth_provider
from app.extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("spa.index"))
    state = secrets.token_urlsafe(32)
    provider = get_oauth_provider("google")
    oauth_url = provider.get_authorization_url(state)
    return render_inertia("auth/Login", props={"oauth_url": oauth_url})


@auth_bp.route("/<provider_name>/login")
def oauth_login(provider_name: str):
    provider = get_oauth_provider(provider_name)
    state = secrets.token_urlsafe(32)
    url = provider.get_authorization_url(state)
    return redirect(url)


@auth_bp.route("/<provider_name>/callback")
def oauth_callback(provider_name: str):
    from flask import request

    code = request.args.get("code")
    if not code:
        return {"error": "Missing code parameter"}, 400

    test_provider = current_app.config.get("_test_oauth_provider")
    provider = test_provider or get_oauth_provider(provider_name)

    service = get_auth_service(provider=provider)
    user = service.login(code=code)
    db.session.commit()

    login_user(user)
    return redirect(url_for("spa.index"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_page"))
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/integration/auth/auth_routes_test.py -v
```

Expected: all 5 tests PASS. (Note: `spa.index` doesn't exist yet — `url_for` call won't fail until the blueprint is registered. If `BuildError` appears, temporarily replace `url_for("spa.index")` with `"/"` and revert after Task 8.)

- [ ] **Step 5: Commit**

```bash
git add app/auth/auth_routes.py tests/integration/auth/auth_routes_test.py
git commit -m "feat: session-based auth routes — login page, callback, logout"
```

---

## Task 5: Update thread routes + tests

**Files:**
- Modify: `app/threads/thread_routes.py`
- Modify: `tests/integration/threads/thread_routes_test.py`

- [ ] **Step 1: Write updated thread route tests**

Replace `tests/integration/threads/thread_routes_test.py`:

```python
import uuid

from app.users.user_model import User
from app.users.user_repository import UserRepository
from tests.conftest import login_as


def _create_user(db_session, email=None):
    repo = UserRepository(db_session)
    if email is None:
        email = f"threads-{uuid.uuid4()}@example.com"
    user = repo.create(User(email=email, display_name="Thread Tester"))
    db_session.commit()
    return user


def test_create_thread(app, client, db_session):
    user = _create_user(db_session)
    login_as(client, user.id)

    response = client.post("/api/threads", json={"name": "general"})
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "general"
    assert data["created_by"] == str(user.id)


def test_create_thread_requires_auth(client):
    response = client.post("/api/threads", json={"name": "general"})
    assert response.status_code == 401


def test_list_threads(app, client, db_session):
    user = _create_user(db_session)
    login_as(client, user.id)

    client.post("/api/threads", json={"name": "thread-1"})
    client.post("/api/threads", json={"name": "thread-2"})

    response = client.get("/api/threads")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2


def test_join_thread(app, client, db_session):
    user1 = _create_user(db_session, f"creator-{uuid.uuid4()}@example.com")
    user2 = _create_user(db_session, f"joiner-{uuid.uuid4()}@example.com")

    login_as(client, user1.id)
    create_resp = client.post("/api/threads", json={"name": "public"})
    thread_id = create_resp.get_json()["id"]

    login_as(client, user2.id)
    join_resp = client.post(f"/api/threads/{thread_id}/join")
    assert join_resp.status_code == 200
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/integration/threads/thread_routes_test.py -v
```

Expected: FAIL — routes still at `/threads`, and `make_auth_header` fixture is gone (conftest no longer provides it).

- [ ] **Step 3: Rewrite thread_routes.py**

Replace `app/threads/thread_routes.py`:

```python
import uuid

from flask import Blueprint, request
from flask_inertia import render_inertia
from flask_login import current_user, login_required

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_message_service, get_thread_service
from app.exceptions import AlreadyAMemberError, ThreadNotFoundError

threads_bp = Blueprint("threads", __name__)


def _serialize_thread(thread):
    return {
        "id": str(thread.id),
        "name": thread.name,
        "created_by": str(thread.created_by),
        "created_at": thread.created_at.isoformat(),
    }


# ── REST routes ───────────────────────────────────────────────────────────────

@threads_bp.route("/api/threads", methods=["POST"])
@require_auth
def create_thread():
    data = request.get_json()
    service = get_thread_service()
    thread = service.create_thread(name=data["name"], user_id=current_user_id())
    return _serialize_thread(thread), 201


@threads_bp.route("/api/threads", methods=["GET"])
@require_auth
def list_threads():
    service = get_thread_service()
    threads = service.list_threads(user_id=current_user_id())
    return [_serialize_thread(t) for t in threads]


@threads_bp.route("/api/threads/<thread_id>/join", methods=["POST"])
@require_auth
def join_thread(thread_id: str):
    service = get_thread_service()
    try:
        service.join_thread(thread_id=uuid.UUID(thread_id), user_id=current_user_id())
    except ThreadNotFoundError:
        return {"error": "Thread not found"}, 404
    except AlreadyAMemberError:
        return {"error": "Already a member"}, 409
    return {"status": "joined"}


# ── Inertia page routes ───────────────────────────────────────────────────────

@threads_bp.route("/threads")
@login_required
def threads_page():
    threads = get_thread_service().list_threads(user_id=current_user.id)
    return render_inertia("threads/ThreadList", props={
        "threads": [_serialize_thread(t) for t in threads],
    })


@threads_bp.route("/threads/<thread_id>")
@login_required
def thread_detail_page(thread_id: str):
    thread = get_thread_service().get_thread(uuid.UUID(thread_id))
    messages = get_message_service().list_messages(uuid.UUID(thread_id), limit=50, offset=0)
    return render_inertia("threads/ThreadDetail", props={
        "thread": _serialize_thread(thread),
        "messages": [
            {
                "id": str(m.id),
                "user_id": str(m.user_id),
                "content": m.content,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    })
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/integration/threads/thread_routes_test.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/threads/thread_routes.py tests/integration/threads/thread_routes_test.py
git commit -m "feat: thread REST routes to /api/threads, add Inertia page routes"
```

---

## Task 6: Update message routes + tests

**Files:**
- Modify: `app/messages/message_routes.py`
- Modify: `tests/integration/messages/message_routes_test.py`

- [ ] **Step 1: Write updated message route tests**

Replace `tests/integration/messages/message_routes_test.py`:

```python
import uuid

from app.users.user_model import User
from app.users.user_repository import UserRepository
from tests.conftest import login_as


def _setup_user_and_thread(client, db_session):
    repo = UserRepository(db_session)
    user = repo.create(
        User(email=f"msg-route-{uuid.uuid4()}@example.com", display_name="Msg Tester")
    )
    db_session.commit()
    login_as(client, user.id)

    resp = client.post("/api/threads", json={"name": "chat"})
    thread_id = resp.get_json()["id"]
    return user, thread_id


def test_send_message(app, client, db_session):
    user, thread_id = _setup_user_and_thread(client, db_session)

    response = client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "hello world"},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["content"] == "hello world"
    assert data["user_id"] == str(user.id)


def test_send_message_requires_membership(app, client, db_session):
    _, thread_id = _setup_user_and_thread(client, db_session)

    repo = UserRepository(db_session)
    outsider = repo.create(
        User(email=f"outsider-{uuid.uuid4()}@example.com", display_name="Outsider")
    )
    db_session.commit()

    outsider_client = app.test_client()
    login_as(outsider_client, outsider.id)

    response = outsider_client.post(
        f"/api/threads/{thread_id}/messages",
        json={"content": "should fail"},
    )
    assert response.status_code == 403


def test_list_messages(app, client, db_session):
    user, thread_id = _setup_user_and_thread(client, db_session)

    client.post(f"/api/threads/{thread_id}/messages", json={"content": "msg 1"})
    client.post(f"/api/threads/{thread_id}/messages", json={"content": "msg 2"})

    response = client.get(f"/api/threads/{thread_id}/messages")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["content"] == "msg 1"
```

- [ ] **Step 2: Run — expect failure**

```bash
uv run pytest tests/integration/messages/message_routes_test.py -v
```

Expected: FAIL — routes still at `/threads/<id>/messages`.

- [ ] **Step 3: Rewrite message_routes.py**

Replace `app/messages/message_routes.py`:

```python
import uuid

from flask import Blueprint, request

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_message_service
from app.exceptions import NotAMemberError, ThreadNotFoundError

messages_bp = Blueprint("messages", __name__)


def _serialize_message(message):
    return {
        "id": str(message.id),
        "thread_id": str(message.thread_id),
        "user_id": str(message.user_id),
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


@messages_bp.route("/api/threads/<thread_id>/messages", methods=["POST"])
@require_auth
def send_message(thread_id: str):
    data = request.get_json()
    service = get_message_service()
    try:
        message = service.send_message(
            user_id=current_user_id(),
            thread_id=uuid.UUID(thread_id),
            content=data["content"],
        )
    except ThreadNotFoundError:
        return {"error": "Thread not found"}, 404
    except NotAMemberError:
        return {"error": "Not a member of this thread"}, 403
    return _serialize_message(message), 201


@messages_bp.route("/api/threads/<thread_id>/messages", methods=["GET"])
@require_auth
def list_messages(thread_id: str):
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)
    service = get_message_service()
    try:
        messages = service.list_messages(
            thread_id=uuid.UUID(thread_id), limit=limit, offset=offset
        )
    except ThreadNotFoundError:
        return {"error": "Thread not found"}, 404
    return [_serialize_message(m) for m in messages]
```

- [ ] **Step 4: Run — expect pass**

```bash
uv run pytest tests/integration/messages/message_routes_test.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app/messages/message_routes.py tests/integration/messages/message_routes_test.py
git commit -m "feat: message REST routes to /api/threads/<id>/messages"
```

---

## Task 7: Update user routes + tests, WebSocket tests, e2e test

**Files:**
- Modify: `app/users/user_routes.py`
- Modify: `tests/integration/users/user_routes_test.py`
- Modify: `tests/integration/messages/message_events_test.py`
- Modify: `tests/e2e/chat_flow_test.py`

- [ ] **Step 1: Write updated user route tests**

Replace `tests/integration/users/user_routes_test.py`:

```python
from app.users.user_model import User
from app.users.user_repository import UserRepository
from tests.conftest import login_as


def test_get_me(app, client, db_session):
    repo = UserRepository(db_session)
    user = repo.create(User(email="me@example.com", display_name="Me"))
    db_session.commit()
    login_as(client, user.id)

    response = client.get("/api/users/me")
    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == "me@example.com"
    assert data["display_name"] == "Me"


def test_get_me_requires_auth(client):
    response = client.get("/api/users/me")
    assert response.status_code == 401
```

- [ ] **Step 2: Rewrite user_routes.py**

Replace `app/users/user_routes.py`:

```python
from flask import Blueprint

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_user_service
from app.exceptions import UserNotFoundError

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


def _serialize_user(user):
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


@users_bp.route("/me", methods=["GET"])
@require_auth
def get_me():
    service = get_user_service()
    try:
        user = service.get_me(current_user_id())
    except UserNotFoundError:
        return {"error": "User not found"}, 404
    return _serialize_user(user)
```

- [ ] **Step 3: Run user route tests — expect pass**

```bash
uv run pytest tests/integration/users/user_routes_test.py -v
```

Expected: both tests PASS.

- [ ] **Step 4: Write updated WebSocket event tests**

Replace `tests/integration/messages/message_events_test.py`:

```python
import uuid

from app.extensions import socketio
from app.threads.thread_model import Thread
from app.threads.thread_repository import ThreadRepository
from app.users.user_model import User
from app.users.user_repository import UserRepository
from tests.conftest import login_as


def _setup(db_session):
    user_repo = UserRepository(db_session)
    thread_repo = ThreadRepository(db_session)

    user = user_repo.create(
        User(email=f"ws-{uuid.uuid4()}@example.com", display_name="WS Tester")
    )
    thread = thread_repo.create(Thread(name="ws-thread", created_by=user.id))
    thread_repo.add_member(thread.id, user.id)
    db_session.commit()
    return user, thread


def test_join_thread_event(app, client, db_session):
    user, thread = _setup(db_session)
    login_as(client, user.id)

    ws_client = socketio.test_client(app, flask_test_client=client)
    assert ws_client.is_connected()

    ws_client.emit("join_thread", {"thread_id": str(thread.id)})
    received = ws_client.get_received()

    assert any(msg["name"] == "thread_joined" for msg in received)
    ws_client.disconnect()


def test_send_message_event_broadcasts(app, client, db_session):
    user, thread = _setup(db_session)
    login_as(client, user.id)

    ws_client = socketio.test_client(app, flask_test_client=client)
    ws_client.emit("join_thread", {"thread_id": str(thread.id)})
    ws_client.get_received()

    ws_client.emit(
        "send_message",
        {"thread_id": str(thread.id), "content": "hello via websocket"},
    )
    received = ws_client.get_received()

    new_message_events = [m for m in received if m["name"] == "new_message"]
    assert len(new_message_events) == 1
    assert new_message_events[0]["args"][0]["content"] == "hello via websocket"
    ws_client.disconnect()


def test_send_message_event_rejected_without_auth(app):
    ws_client = socketio.test_client(app)
    assert not ws_client.is_connected()
```

- [ ] **Step 5: Write updated e2e test**

Replace `tests/e2e/chat_flow_test.py`:

```python
"""
End-to-end test: full chat flow through REST and WebSocket (session-based auth).

1. Two users authenticate via OAuth callback (separate clients = separate sessions)
2. User 1 creates a thread via REST
3. User 2 joins the thread via REST
4. Both connect via WebSocket using their session cookies
5. User 1 sends a message; User 2 receives it
6. Messages are retrievable via REST
"""

from app.auth.oauth import FakeOAuthProvider, OAuthUserInfo
from app.extensions import socketio
from app.users.user_repository import UserRepository


def _login_user(app, client, email, display_name, provider_id):
    """Log in via OAuth callback; the session cookie is set on the client."""
    app.config["_test_oauth_provider"] = FakeOAuthProvider(
        OAuthUserInfo(
            email=email,
            display_name=display_name,
            avatar_url=None,
            provider="google",
            provider_id=provider_id,
        )
    )
    client.get("/auth/google/callback?code=fake&state=test")


def test_full_chat_flow(app, db_session):
    # Each user has their own client to maintain separate sessions
    client1 = app.test_client()
    client2 = app.test_client()

    # Step 1: Authenticate both users
    _login_user(app, client1, "alice@example.com", "Alice", "g-alice")
    _login_user(app, client2, "bob@example.com", "Bob", "g-bob")

    repo = UserRepository(db_session)
    user1 = repo.find_by_email("alice@example.com")

    # Step 2: Alice creates a thread
    create_resp = client1.post("/api/threads", json={"name": "project-chat"})
    assert create_resp.status_code == 201
    thread_id = create_resp.get_json()["id"]

    # Step 3: Bob joins the thread
    join_resp = client2.post(f"/api/threads/{thread_id}/join")
    assert join_resp.status_code == 200

    # Step 4: Both connect via WebSocket (session is shared with the Flask test client)
    ws1 = socketio.test_client(app, flask_test_client=client1)
    ws2 = socketio.test_client(app, flask_test_client=client2)

    assert ws1.is_connected()
    assert ws2.is_connected()

    ws1.emit("join_thread", {"thread_id": thread_id})
    ws2.emit("join_thread", {"thread_id": thread_id})
    ws1.get_received()
    ws2.get_received()

    # Step 5: Alice sends, Bob receives
    ws1.emit("send_message", {"thread_id": thread_id, "content": "Hey Bob!"})

    bob_received = ws2.get_received()
    new_messages = [m for m in bob_received if m["name"] == "new_message"]
    assert len(new_messages) == 1
    assert new_messages[0]["args"][0]["content"] == "Hey Bob!"
    assert new_messages[0]["args"][0]["user_id"] == str(user1.id)

    # Step 6: REST retrieval
    list_resp = client2.get(f"/api/threads/{thread_id}/messages")
    assert list_resp.status_code == 200
    messages = list_resp.get_json()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hey Bob!"

    ws1.disconnect()
    ws2.disconnect()
```

- [ ] **Step 6: Run all updated tests**

```bash
uv run pytest tests/integration tests/e2e -v
```

Expected: all tests PASS. If WebSocket tests fail with session issues, verify `flask_test_client=client` is passed correctly and that `login_as` was called before creating the WS test client.

- [ ] **Step 7: Commit**

```bash
git add app/users/user_routes.py \
        tests/integration/users/user_routes_test.py \
        tests/integration/messages/message_events_test.py \
        tests/e2e/chat_flow_test.py
git commit -m "feat: user routes to /api/users, session-based WS auth, update e2e test"
```

---

## Task 8: Create SPA blueprint, root template, and wire create_app

**Files:**
- Create: `app/spa/__init__.py`
- Create: `app/spa/spa_routes.py`
- Create: `app/templates/spa_root.html`
- Modify: `app/__init__.py`

- [ ] **Step 1: Create spa/__init__.py**

```python
```

(empty file — just makes it a package)

- [ ] **Step 2: Create spa_routes.py**

Create `app/spa/spa_routes.py`:

```python
from flask import Blueprint
from flask_inertia import render_inertia
from flask_login import login_required

spa_bp = Blueprint("spa", __name__)


@spa_bp.route("/", defaults={"path": ""})
@spa_bp.route("/<path:path>")
@login_required
def index(path: str):
    return render_inertia("home/Home", props={})
```

- [ ] **Step 3: Create spa_root.html**

Create `app/templates/spa_root.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {{ inertia_head() }}
    {% if config.DEBUG %}
      <script type="module" src="http://localhost:5173/@vite/client"></script>
    {% elif vite_manifest %}
      {% set entry = vite_manifest.get('src/main.tsx', {}) %}
      {% for css in entry.get('css', []) %}
        <link rel="stylesheet" href="{{ url_for('static', filename='dist/' + css) }}" />
      {% endfor %}
    {% endif %}
  </head>
  <body>
    {{ inertia() }}
    {% if config.DEBUG %}
      <script type="module" src="http://localhost:5173/src/main.tsx"></script>
    {% elif vite_manifest %}
      {% set entry = vite_manifest.get('src/main.tsx', {}) %}
      <script type="module" src="{{ url_for('static', filename='dist/' + entry.get('file', '')) }}"></script>
    {% endif %}
  </body>
</html>
```

- [ ] **Step 4: Rewrite create_app in __init__.py**

Replace `app/__init__.py`:

```python
import json
from pathlib import Path

from flask import Flask

from app.config import DevConfig
from app.extensions import db, inertia, login_manager, migrate, socketio


def create_app(config=None):
    flask_app = Flask(__name__, template_folder="templates")
    flask_app.config.from_object(config or DevConfig)

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    socketio.init_app(flask_app, cors_allowed_origins="*")
    inertia.init_app(flask_app)
    flask_app.config["INERTIA_TEMPLATE"] = "spa_root.html"

    login_manager.init_app(flask_app)
    login_manager.login_view = "auth.login_page"

    @login_manager.user_loader
    def load_user(user_id: str):
        import uuid

        from app.users.user_model import User

        return db.session.get(User, uuid.UUID(user_id))

    # Expose Vite manifest to templates for asset linking in production
    @flask_app.context_processor
    def vite_context():
        manifest_path = (
            Path(flask_app.static_folder or "app/static") / "dist" / ".vite" / "manifest.json"
        )
        if manifest_path.exists():
            return {"vite_manifest": json.loads(manifest_path.read_text())}
        return {"vite_manifest": {}}

    with flask_app.app_context():
        import app.messages.message_model  # noqa: F401
        import app.threads.thread_member_model  # noqa: F401
        import app.threads.thread_model  # noqa: F401
        import app.users.user_model  # noqa: F401
        import app.users.user_oauth_account_model  # noqa: F401

    from app.auth.auth_routes import auth_bp
    from app.messages.message_routes import messages_bp
    from app.spa.spa_routes import spa_bp
    from app.threads.thread_routes import threads_bp
    from app.users.user_routes import users_bp

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(threads_bp)
    flask_app.register_blueprint(messages_bp)
    flask_app.register_blueprint(users_bp)
    flask_app.register_blueprint(spa_bp)  # must be last — catch-all route

    import app.messages.message_events  # noqa: F401, E402

    return flask_app
```

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest -q
```

Expected: all tests PASS. If auth route tests fail on `url_for("spa.index")`, confirm `spa_bp` is registered and the endpoint name matches (`spa.index` is the function name in `spa_routes.py`).

- [ ] **Step 6: Commit**

```bash
git add app/spa/ app/templates/spa_root.html app/__init__.py
git commit -m "feat: SPA blueprint with catch-all route and Inertia root template"
```

---

## Task 9: Scaffold frontend Vite project

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`

- [ ] **Step 1: Create frontend/package.json**

```json
{
  "name": "flask-example-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "lint": "eslint src",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "@inertiajs/react": "^2.0.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "socket.io-client": "^4.8.1"
  },
  "devDependencies": {
    "@eslint/js": "^9.17.0",
    "@tailwindcss/vite": "^4.0.0",
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "eslint": "^9.17.0",
    "eslint-plugin-react-hooks": "^5.0.0",
    "tailwindcss": "^4.0.0",
    "typescript": "^5.7.2",
    "typescript-eslint": "^8.18.2",
    "vite": "^6.0.5"
  }
}
```

- [ ] **Step 2: Create frontend/vite.config.ts**

```ts
import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': path.resolve(__dirname, 'src') },
  },
  build: {
    outDir: '../app/static/dist',
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: 'index.html',
    },
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/auth': 'http://localhost:5000',
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
      },
    },
  },
})
```

- [ ] **Step 3: Create frontend/tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create frontend/index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Chat</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create frontend/src/index.css**

```css
@import "tailwindcss";
```

- [ ] **Step 6: Create frontend/src/main.tsx**

```tsx
import './index.css'
import { createInertiaApp } from '@inertiajs/react'
import { createRoot } from 'react-dom/client'

createInertiaApp({
  resolve: (name) => {
    const pages = import.meta.glob('./pages/**/*.page.tsx', { eager: true })
    return pages[`./pages/${name}.page.tsx`] as any
  },
  setup({ el, App, props }) {
    createRoot(el).render(<App {...props} />)
  },
})
```

- [ ] **Step 7: Install dependencies**

```bash
cd frontend && pnpm install
```

Expected: `node_modules/` created, `pnpm-lock.yaml` generated.

- [ ] **Step 8: Verify TypeScript compiles**

```bash
cd frontend && pnpm typecheck
```

Expected: exits 0 (no errors — only `src/main.tsx` exists and it imports from packages that are now installed).

- [ ] **Step 9: Commit**

```bash
cd ..
git add frontend/package.json frontend/vite.config.ts frontend/tsconfig.json \
        frontend/index.html frontend/src/index.css frontend/src/main.tsx \
        frontend/pnpm-lock.yaml
git commit -m "feat: scaffold Vite + React + Inertia frontend"
```

---

## Task 10: Configure shadcn and add Button component

**Files:**
- Create: `frontend/components.json`
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/button.tsx`

- [ ] **Step 1: Create components.json**

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components",
    "lib": "@/lib",
    "hooks": "@/hooks"
  }
}
```

- [ ] **Step 2: Install shadcn peer dependencies and add Button**

```bash
cd frontend && pnpm add class-variance-authority clsx tailwind-merge
pnpm add lucide-react
pnpm dlx shadcn@latest add button --yes
```

Expected: creates `src/components/button.tsx` and `src/lib/utils.ts`.

If the shadcn CLI creates `src/components/ui/button.tsx` instead of `src/components/button.tsx`, move it:

```bash
mv src/components/ui/button.tsx src/components/button.tsx
rmdir src/components/ui 2>/dev/null || true
```

Then update `src/components/button.tsx` to fix the import if it references `@/components/ui/utils` — change it to `@/lib/utils`.

- [ ] **Step 3: Verify lib/utils.ts exists**

Confirm `frontend/src/lib/utils.ts` was created by shadcn. If not, create it:

```ts
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

- [ ] **Step 4: Verify TypeScript compiles**

```bash
cd frontend && pnpm typecheck
```

Expected: exits 0.

- [ ] **Step 5: Commit**

```bash
cd ..
git add frontend/components.json frontend/src/lib/ frontend/src/components/ \
        frontend/package.json frontend/pnpm-lock.yaml
git commit -m "feat: configure shadcn with Button component output to src/components/"
```

---

## Task 11: Create stub pages and shared hooks

**Files:**
- Create: `frontend/src/pages/auth/Login.page.tsx`
- Create: `frontend/src/pages/auth/Login.layout.tsx`
- Create: `frontend/src/pages/home/Home.page.tsx`
- Create: `frontend/src/pages/home/Home.layout.tsx`
- Create: `frontend/src/pages/threads/ThreadList.page.tsx`
- Create: `frontend/src/pages/threads/ThreadList.layout.tsx`
- Create: `frontend/src/pages/threads/ThreadDetail.page.tsx`
- Create: `frontend/src/pages/threads/ThreadDetail.layout.tsx`
- Create: `frontend/src/hooks/useSocket.ts`
- Create: `frontend/src/hooks/useLocalStorage.ts`

- [ ] **Step 1: Create Login.page.tsx**

```tsx
import { usePage } from '@inertiajs/react'
import { LoginLayout } from './Login.layout'

interface LoginPageProps {
  oauth_url: string
}

export default function LoginPage() {
  const { oauth_url } = usePage<LoginPageProps>().props
  return <LoginLayout oauthUrl={oauth_url} />
}
```

- [ ] **Step 2: Create Login.layout.tsx**

```tsx
import { Button } from '@/components/button'

interface LoginLayoutProps {
  oauthUrl: string
}

export function LoginLayout({ oauthUrl }: LoginLayoutProps) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center gap-6 p-8">
        <h1 className="text-2xl font-bold">Welcome to Chat</h1>
        <a href={oauthUrl}>
          <Button>Sign in with Google</Button>
        </a>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create Home.page.tsx**

```tsx
import { usePage } from '@inertiajs/react'
import { HomeLayout } from './Home.layout'

interface HomePageProps {
  user: { display_name: string }
}

export default function HomePage() {
  const { user } = usePage<HomePageProps>().props
  return <HomeLayout user={user} />
}
```

- [ ] **Step 4: Create Home.layout.tsx**

```tsx
import { Button } from '@/components/button'

interface HomeLayoutProps {
  user: { display_name: string }
}

export function HomeLayout({ user }: HomeLayoutProps) {
  return (
    <div className="min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-4">Hello, {user.display_name}</h1>
      <a href="/threads">
        <Button>View Threads</Button>
      </a>
    </div>
  )
}
```

- [ ] **Step 5: Update spa_routes.py to pass user prop to Home**

The Home page needs a `user` prop. Update `app/spa/spa_routes.py`:

```python
from flask import Blueprint
from flask_inertia import render_inertia
from flask_login import current_user, login_required

spa_bp = Blueprint("spa", __name__)


@spa_bp.route("/", defaults={"path": ""})
@spa_bp.route("/<path:path>")
@login_required
def index(path: str):
    return render_inertia(
        "home/Home",
        props={
            "user": {
                "display_name": current_user.display_name,
            }
        },
    )
```

- [ ] **Step 6: Create ThreadList.page.tsx**

```tsx
import { usePage } from '@inertiajs/react'
import { ThreadListLayout } from './ThreadList.layout'

interface Thread {
  id: string
  name: string
  created_by: string
  created_at: string
}

interface ThreadListPageProps {
  threads: Thread[]
}

export default function ThreadListPage() {
  const { threads } = usePage<ThreadListPageProps>().props
  return <ThreadListLayout threads={threads} />
}
```

- [ ] **Step 7: Create ThreadList.layout.tsx**

```tsx
import { Button } from '@/components/button'

interface Thread {
  id: string
  name: string
  created_at: string
}

interface ThreadListLayoutProps {
  threads: Thread[]
}

export function ThreadListLayout({ threads }: ThreadListLayoutProps) {
  return (
    <div className="min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-6">Threads</h1>
      <ul className="flex flex-col gap-2">
        {threads.map((thread) => (
          <li key={thread.id}>
            <a href={`/threads/${thread.id}`}>
              <Button variant="outline" className="w-full justify-start">
                {thread.name}
              </Button>
            </a>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 8: Create ThreadDetail.page.tsx**

```tsx
import { usePage } from '@inertiajs/react'
import { useEffect, useState } from 'react'
import { io } from 'socket.io-client'
import { ThreadDetailLayout } from './ThreadDetail.layout'

interface Thread {
  id: string
  name: string
}

interface Message {
  id: string
  user_id: string
  content: string
  created_at: string
}

interface ThreadDetailPageProps {
  thread: Thread
  messages: Message[]
}

export default function ThreadDetailPage() {
  const { thread, messages: initial } = usePage<ThreadDetailPageProps>().props
  const [messages, setMessages] = useState<Message[]>(initial)

  useEffect(() => {
    const socket = io()
    socket.emit('join_thread', { thread_id: thread.id })
    socket.on('new_message', (msg: Message) => {
      setMessages((prev) => [...prev, msg])
    })
    return () => {
      socket.disconnect()
    }
  }, [thread.id])

  return <ThreadDetailLayout thread={thread} messages={messages} />
}
```

- [ ] **Step 9: Create ThreadDetail.layout.tsx**

```tsx
interface Thread {
  id: string
  name: string
}

interface Message {
  id: string
  user_id: string
  content: string
  created_at: string
}

interface ThreadDetailLayoutProps {
  thread: Thread
  messages: Message[]
}

export function ThreadDetailLayout({ thread, messages }: ThreadDetailLayoutProps) {
  return (
    <div className="min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-6">{thread.name}</h1>
      <ul className="flex flex-col gap-2">
        {messages.map((msg) => (
          <li key={msg.id} className="p-3 rounded border">
            <p className="text-sm text-muted-foreground">{msg.user_id}</p>
            <p>{msg.content}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}
```

- [ ] **Step 10: Create useSocket.ts**

```ts
import { useEffect, useRef } from 'react'
import { io, Socket } from 'socket.io-client'

export function useSocket(): Socket {
  const socketRef = useRef<Socket | null>(null)

  if (!socketRef.current) {
    socketRef.current = io()
  }

  useEffect(() => {
    return () => {
      socketRef.current?.disconnect()
      socketRef.current = null
    }
  }, [])

  return socketRef.current
}
```

- [ ] **Step 11: Create useLocalStorage.ts**

```ts
import { useState } from 'react'

export function useLocalStorage<T>(key: string, initial: T): [T, (value: T) => void] {
  const [stored, setStored] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key)
      return item ? (JSON.parse(item) as T) : initial
    } catch {
      return initial
    }
  })

  function setValue(value: T) {
    setStored(value)
    window.localStorage.setItem(key, JSON.stringify(value))
  }

  return [stored, setValue]
}
```

- [ ] **Step 12: Verify TypeScript compiles**

```bash
cd frontend && pnpm typecheck
```

Expected: exits 0 — no type errors across all page and hook files.

- [ ] **Step 13: Commit**

```bash
cd ..
git add app/spa/spa_routes.py frontend/src/
git commit -m "feat: stub pages with page/layout split, useSocket and useLocalStorage hooks"
```

---

## Task 12: Update Makefile, lefthook, and .gitignore

**Files:**
- Modify: `Makefile`
- Modify: `lefthook.yml`
- Modify: `.gitignore`

- [ ] **Step 1: Replace Makefile**

```makefile
.PHONY: dev run test test-unit test-integration test-e2e lint format typecheck migrate migrate-new \
        db-up frontend-install frontend-dev frontend-build

db-up:
	docker compose up -d postgres

run:
	uv run flask --app app:create_app run --debug

frontend-dev:
	cd frontend && pnpm dev

frontend-build:
	cd frontend && pnpm build

frontend-install:
	cd frontend && pnpm install

dev: db-up
	make -j2 run frontend-dev

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

test-e2e:
	uv run pytest tests/e2e

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check

migrate:
	uv run flask --app app:create_app db upgrade

migrate-new:
	uv run flask --app app:create_app db migrate -m "$(msg)"
```

- [ ] **Step 2: Update lefthook.yml**

```yaml
pre-commit:
  parallel: true
  commands:
    ruff-format:
      glob: "**/*.py"
      run: uv run ruff format --check {staged_files}
    ruff-lint:
      glob: "**/*.py"
      run: uv run ruff check {staged_files}
    frontend-lint:
      glob: "frontend/src/**/*.{ts,tsx}"
      run: cd frontend && pnpm lint
    frontend-typecheck:
      glob: "frontend/src/**/*.{ts,tsx}"
      run: cd frontend && pnpm typecheck

pre-push:
  parallel: true
  commands:
    typecheck:
      run: uv run ty check
    test-unit:
      run: uv run pytest tests/unit -q
```

- [ ] **Step 3: Add entries to .gitignore**

Add to the end of `.gitignore`:

```
# Frontend build output (generated by vite build)
app/static/dist/

# Node
frontend/node_modules/
frontend/.pnpm-debug.log*
```

- [ ] **Step 4: Commit**

```bash
git add Makefile lefthook.yml .gitignore
git commit -m "chore: update Makefile, lefthook, gitignore for frontend"
```

---

## Task 13: Update Dockerfile and docker-compose.yml

**Files:**
- Modify: `Dockerfile`
- Modify: `docker-compose.yml`

- [ ] **Step 1: Replace Dockerfile with multi-stage build**

```dockerfile
# Stage 1: Frontend build
# Uses /build/frontend as workdir so '../app/static/dist' resolves to /build/app/static/dist
FROM node:22-slim AS frontend-builder
WORKDIR /build/frontend
RUN npm install -g pnpm
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ .
RUN pnpm build

# Stage 2: Python base
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Stage 3: Python dependencies
FROM base AS deps
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Stage 4: Runtime
FROM base AS runtime
WORKDIR /app
COPY --from=deps /app/.venv /app/.venv
COPY . .
COPY --from=frontend-builder /build/app/static/dist ./app/static/dist
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 5000
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "wsgi:app"]
```

- [ ] **Step 2: Update docker-compose.yml — remove JWT_SECRET**

In `docker-compose.yml`, remove `JWT_SECRET` from the `app` service environment block:

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: chat
      POSTGRES_PASSWORD: chat
      POSTGRES_DB: chat
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "chat"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "${APP_PORT:-5001}:5000"
    command: >
      sh -c "flask --app wsgi:app db upgrade &&
      exec gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 wsgi:app"
    environment:
      DATABASE_URL: postgresql://chat:chat@postgres:5432/chat
      SECRET_KEY: ${SECRET_KEY:-dev-secret-key}
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID:-}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET:-}
      GOOGLE_REDIRECT_URI: ${GOOGLE_REDIRECT_URI:-}
      GITHUB_CLIENT_ID: ${GITHUB_CLIENT_ID:-}
      GITHUB_CLIENT_SECRET: ${GITHUB_CLIENT_SECRET:-}
      GITHUB_REDIRECT_URI: ${GITHUB_REDIRECT_URI:-}
    depends_on:
      postgres:
        condition: service_healthy

volumes:
  pgdata:
```

- [ ] **Step 3: Verify Docker build**

```bash
docker build -t flask-example-test .
```

Expected: all 4 stages complete successfully. The frontend build stage runs `pnpm build`, producing assets in `/build/app/static/dist/`, which are then copied into the runtime image.

- [ ] **Step 4: Run full test suite one final time**

```bash
uv run pytest -q
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add Dockerfile docker-compose.yml
git commit -m "feat: multi-stage Docker build with Node frontend stage, remove JWT_SECRET from compose"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** Flask-Login sessions ✓, flask-inertia ✓, page/layout convention ✓, shadcn to `src/components/` ✓, Tailwind v4 ✓, pnpm ✓, `make dev` starts Postgres + Flask + Vite ✓, Dockerfile multi-stage ✓, lefthook frontend hooks ✓, `spa_root.html` at `app/templates/` ✓, `login_manager.login_view` set ✓, spa_bp registered last ✓, vite manifest context processor ✓
- [x] **No placeholders:** All steps include complete code
- [x] **Type consistency:** `current_user_id()` returns `uuid.UUID` throughout; `login()` returns `User` in all tasks; route URLs consistent (`/api/threads` in routes, tests, and e2e)
- [x] **Catch-all conflict:** spa_bp registered last — domain blueprints match `/api/threads`, `/auth/...`, `/threads/...` first
- [x] **login_manager.login_view:** Set to `"auth.login_page"` in `create_app`
- [x] **vite alias:** Uses `path.resolve(__dirname, 'src')` not `/src`

**Plan complete and saved to `docs/superpowers/plans/2026-04-12-react-frontend.md`.**
