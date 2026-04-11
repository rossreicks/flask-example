# Flask Chat Application Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a testable Flask chat application (Slack-style) with clean layered architecture, demonstrating repository pattern, OAuth, websockets, and three layers of testing.

**Architecture:** Domain-based folder structure with layered architecture (routes/events → services → repositories → models). Factory functions for dependency injection. RepositorySession protocol enforced by ty type checker to prevent repositories from committing transactions.

**Tech Stack:** Flask, Flask-SocketIO, Flask-SQLAlchemy, Alembic, PostgreSQL, testcontainers, pytest, uv, Ruff, ty, Lefthook, Docker

---

## File Map

### Project Root
- `pyproject.toml` — dependencies, tool config (pytest, ruff, ty)
- `Makefile` — common commands
- `Dockerfile` — multi-stage build
- `docker-compose.yml` — postgres + app
- `lefthook.yml` — git hooks

### App Core (`app/`)
- `app/__init__.py` — app factory (`create_app`)
- `app/config.py` — config classes (Dev, Test, Prod)
- `app/extensions.py` — SQLAlchemy, SocketIO, Migrate singletons
- `app/dependencies.py` — factory functions for building services
- `app/exceptions.py` — custom domain exceptions

### Auth Domain (`app/auth/`)
- `app/auth/__init__.py`
- `app/auth/oauth.py` — OAuthProvider protocol, OAuthUserInfo, Google/GitHub implementations, FakeOAuthProvider
- `app/auth/jwt.py` — JWT encode/decode utilities
- `app/auth/decorators.py` — `@require_auth`, `@require_socket_auth`
- `app/auth/auth_service.py` — login/link flow
- `app/auth/auth_routes.py` — OAuth login/callback endpoints

### Users Domain (`app/users/`)
- `app/users/__init__.py`
- `app/users/user_model.py` — User model
- `app/users/user_oauth_account_model.py` — UserOAuthAccount model
- `app/users/user_repository.py` — UserRepository
- `app/users/user_oauth_account_repository.py` — UserOAuthAccountRepository
- `app/users/user_service.py` — UserService
- `app/users/user_routes.py` — user endpoints

### Threads Domain (`app/threads/`)
- `app/threads/__init__.py`
- `app/threads/thread_model.py` — Thread model
- `app/threads/thread_member_model.py` — ThreadMember model
- `app/threads/thread_repository.py` — ThreadRepository
- `app/threads/thread_service.py` — ThreadService
- `app/threads/thread_routes.py` — thread endpoints

### Messages Domain (`app/messages/`)
- `app/messages/__init__.py`
- `app/messages/message_model.py` — Message model
- `app/messages/message_repository.py` — MessageRepository
- `app/messages/message_service.py` — MessageService
- `app/messages/message_routes.py` — message endpoints
- `app/messages/message_events.py` — SocketIO event handlers

### Tests (`tests/`)
- `tests/conftest.py` — shared fixtures (app, db, auth helpers)
- `tests/unit/auth/auth_service_test.py`
- `tests/unit/users/user_repository_test.py`
- `tests/unit/users/user_oauth_account_repository_test.py`
- `tests/unit/users/user_service_test.py`
- `tests/unit/threads/thread_repository_test.py`
- `tests/unit/threads/thread_service_test.py`
- `tests/unit/messages/message_repository_test.py`
- `tests/unit/messages/message_service_test.py`
- `tests/integration/auth/auth_routes_test.py`
- `tests/integration/users/user_routes_test.py`
- `tests/integration/threads/thread_routes_test.py`
- `tests/integration/messages/message_routes_test.py`
- `tests/integration/messages/message_events_test.py`
- `tests/e2e/chat_flow_test.py`

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/extensions.py`

- [ ] **Step 1: Initialize uv project**

```bash
cd /Users/ross/projects/flask-example
uv init --no-readme
```

- [ ] **Step 2: Replace pyproject.toml with full config**

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
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "pyjwt>=2.9",
    "requests>=2.32",
    "python-dotenv>=1.0",
    "gunicorn>=23.0",
    "eventlet>=0.37",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "pytest-cov>=6.0",
    "testcontainers[postgres]>=4.9",
    "ruff>=0.9",
    "ty>=0.0.1a7",
]

[tool.pytest.ini_options]
python_files = "*_test.py"
python_functions = "test_*"
testpaths = ["tests"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "W", "I", "T20", "UP"]

[tool.ruff.format]
quote-style = "double"
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

- [ ] **Step 4: Create app/config.py**

```python
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://localhost:5432/chat")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET = os.environ.get("JWT_SECRET", "dev-jwt-secret")
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
    JWT_SECRET = "test-jwt-secret"


class ProdConfig(Config):
    DEBUG = False
```

- [ ] **Step 5: Create app/extensions.py**

```python
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
socketio = SocketIO()
migrate = Migrate()
```

- [ ] **Step 6: Create app/__init__.py with app factory**

```python
from flask import Flask

from app.config import DevConfig
from app.extensions import db, migrate, socketio


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or DevConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    return app
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock app/__init__.py app/config.py app/extensions.py .python-version
git commit -m "feat: project scaffolding with uv, Flask app factory, config, extensions"
```

---

### Task 2: Docker Compose, Dockerfile, Makefile, Lefthook

**Files:**
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `Makefile`
- Create: `lefthook.yml`
- Create: `.env.example`

- [ ] **Step 1: Create docker-compose.yml**

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
      test: ["CMD-ONLY", "pg_isready", "-U", "chat"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      DATABASE_URL: postgresql://chat:chat@postgres:5432/chat
      SECRET_KEY: ${SECRET_KEY:-dev-secret-key}
      JWT_SECRET: ${JWT_SECRET:-dev-jwt-secret}
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

- [ ] **Step 2: Create Dockerfile**

```dockerfile
# Stage 1: Base
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*

# Stage 2: Dependencies
FROM base AS deps
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Stage 3: App
FROM base AS runtime
WORKDIR /app
COPY --from=deps /app/.venv /app/.venv
COPY . .
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 5000
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "app:create_app()"]
```

- [ ] **Step 3: Create Makefile**

```makefile
.PHONY: dev test test-unit test-integration test-e2e lint format typecheck migrate

dev:
	uv run flask --app app:create_app run --debug

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

- [ ] **Step 4: Create lefthook.yml**

```yaml
pre-commit:
  parallel: true
  commands:
    ruff-format:
      run: uv run ruff format --check .
    ruff-lint:
      run: uv run ruff check .

pre-push:
  parallel: true
  commands:
    typecheck:
      run: uv run ty check
    test-unit:
      run: uv run pytest tests/unit -q
```

- [ ] **Step 5: Create .env.example**

```
SECRET_KEY=change-me
JWT_SECRET=change-me
DATABASE_URL=postgresql://chat:chat@localhost:5432/chat
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/google/callback
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:5000/auth/github/callback
```

- [ ] **Step 6: Create .gitignore**

```
__pycache__/
*.py[cod]
.venv/
.env
*.egg-info/
dist/
.pytest_cache/
.ruff_cache/
```

- [ ] **Step 7: Install lefthook and activate**

```bash
brew install lefthook  # or: uv tool install lefthook
lefthook install
```

- [ ] **Step 8: Commit**

```bash
git add docker-compose.yml Dockerfile Makefile lefthook.yml .env.example .gitignore
git commit -m "feat: add Docker, docker-compose, Makefile, lefthook, gitignore"
```

---

### Task 3: Data Models and Initial Migration

**Files:**
- Create: `app/users/__init__.py`
- Create: `app/users/user_model.py`
- Create: `app/users/user_oauth_account_model.py`
- Create: `app/threads/__init__.py`
- Create: `app/threads/thread_model.py`
- Create: `app/threads/thread_member_model.py`
- Create: `app/messages/__init__.py`
- Create: `app/messages/message_model.py`

- [ ] **Step 1: Create app/users/__init__.py**

```python
```

(Empty `__init__.py` — same for threads and messages.)

- [ ] **Step 2: Create app/users/user_model.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    oauth_accounts: Mapped[list["UserOAuthAccount"]] = relationship(back_populates="user")
```

- [ ] **Step 3: Create app/users/user_oauth_account_model.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class UserOAuthAccount(db.Model):
    __tablename__ = "user_oauth_accounts"
    __table_args__ = (UniqueConstraint("provider", "provider_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_id: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")
```

- [ ] **Step 4: Create app/threads/thread_model.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Thread(db.Model):
    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    creator: Mapped["User"] = relationship()
    members: Mapped[list["ThreadMember"]] = relationship(back_populates="thread")
```

- [ ] **Step 5: Create app/threads/thread_member_model.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class ThreadMember(db.Model):
    __tablename__ = "thread_members"

    thread_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("threads.id"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    thread: Mapped["Thread"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()
```

- [ ] **Step 6: Create app/messages/message_model.py**

```python
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db


class Message(db.Model):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.utcnow)

    thread: Mapped["Thread"] = relationship()
    user: Mapped["User"] = relationship()
```

- [ ] **Step 7: Import all models in app factory so Alembic sees them**

Update `app/__init__.py`:

```python
from flask import Flask

from app.config import DevConfig
from app.extensions import db, migrate, socketio


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or DevConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    with app.app_context():
        import app.users.user_model  # noqa: F401
        import app.users.user_oauth_account_model  # noqa: F401
        import app.threads.thread_model  # noqa: F401
        import app.threads.thread_member_model  # noqa: F401
        import app.messages.message_model  # noqa: F401

    return app
```

- [ ] **Step 8: Generate initial migration**

Start postgres first, then generate:

```bash
docker compose up -d postgres
DATABASE_URL=postgresql://chat:chat@localhost:5432/chat uv run flask --app app:create_app db init
DATABASE_URL=postgresql://chat:chat@localhost:5432/chat uv run flask --app app:create_app db migrate -m "initial models"
DATABASE_URL=postgresql://chat:chat@localhost:5432/chat uv run flask --app app:create_app db upgrade
```

- [ ] **Step 9: Commit**

```bash
git add app/ migrations/
git commit -m "feat: add data models (User, UserOAuthAccount, Thread, ThreadMember, Message) and initial migration"
```

---

### Task 4: Test Infrastructure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/integration/__init__.py`
- Create: `tests/e2e/__init__.py`

- [ ] **Step 1: Create test directory structure**

```bash
mkdir -p tests/unit/users tests/unit/threads tests/unit/messages tests/unit/auth
mkdir -p tests/integration/users tests/integration/threads tests/integration/messages tests/integration/auth
mkdir -p tests/e2e
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py tests/e2e/__init__.py
touch tests/unit/users/__init__.py tests/unit/threads/__init__.py tests/unit/messages/__init__.py tests/unit/auth/__init__.py
touch tests/integration/users/__init__.py tests/integration/threads/__init__.py tests/integration/messages/__init__.py tests/integration/auth/__init__.py
```

- [ ] **Step 2: Create tests/conftest.py**

```python
import uuid

import jwt
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


def make_jwt(user_id: uuid.UUID, app) -> str:
    return jwt.encode(
        {"sub": str(user_id)},
        app.config["JWT_SECRET"],
        algorithm="HS256",
    )


@pytest.fixture
def make_auth_header(app):
    def _make(user_id: uuid.UUID) -> dict:
        token = make_jwt(user_id, app)
        return {"Authorization": f"Bearer {token}"}

    return _make
```

- [ ] **Step 3: Write a smoke test to verify infrastructure**

Create `tests/unit/smoke_test.py`:

```python
from app.extensions import db


def test_database_is_reachable(db_session):
    result = db_session.execute(db.text("SELECT 1"))
    assert result.scalar() == 1
```

- [ ] **Step 4: Run the smoke test**

```bash
uv run pytest tests/unit/smoke_test.py -v
```

Expected: PASS — testcontainers spins up postgres, app creates tables, session works.

- [ ] **Step 5: Commit**

```bash
git add tests/
git commit -m "feat: test infrastructure with testcontainers postgres, session fixtures, JWT helpers"
```

---

### Task 5: RepositorySession Protocol and Custom Exceptions

**Files:**
- Create: `app/repositories.py`
- Create: `app/exceptions.py`

- [ ] **Step 1: Create app/repositories.py with RepositorySession protocol**

```python
from typing import Any, Protocol

from sqlalchemy import Result


class RepositorySession(Protocol):
    def add(self, instance: Any) -> None: ...
    def delete(self, instance: Any) -> None: ...
    def get(self, entity: Any, ident: Any) -> Any: ...
    def execute(self, statement: Any) -> Result[Any]: ...
    def flush(self) -> None: ...
    def scalar(self, statement: Any) -> Any: ...
    def scalars(self, statement: Any) -> Any: ...
```

- [ ] **Step 2: Create app/exceptions.py**

```python
import uuid


class NotFoundError(Exception):
    def __init__(self, entity: str, entity_id: uuid.UUID):
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} {entity_id} not found")


class UserNotFoundError(NotFoundError):
    def __init__(self, user_id: uuid.UUID):
        super().__init__("User", user_id)


class ThreadNotFoundError(NotFoundError):
    def __init__(self, thread_id: uuid.UUID):
        super().__init__("Thread", thread_id)


class NotAMemberError(Exception):
    def __init__(self, user_id: uuid.UUID, thread_id: uuid.UUID):
        self.user_id = user_id
        self.thread_id = thread_id
        super().__init__(f"User {user_id} is not a member of thread {thread_id}")


class AlreadyAMemberError(Exception):
    def __init__(self, user_id: uuid.UUID, thread_id: uuid.UUID):
        self.user_id = user_id
        self.thread_id = thread_id
        super().__init__(f"User {user_id} is already a member of thread {thread_id}")


class OAuthError(Exception):
    pass
```

- [ ] **Step 3: Commit**

```bash
git add app/repositories.py app/exceptions.py
git commit -m "feat: add RepositorySession protocol and custom domain exceptions"
```

---

### Task 6: User Repository (TDD)

**Files:**
- Create: `app/users/user_repository.py`
- Create: `app/users/user_oauth_account_repository.py`
- Create: `tests/unit/users/user_repository_test.py`
- Create: `tests/unit/users/user_oauth_account_repository_test.py`

- [ ] **Step 1: Write failing tests for UserRepository**

Create `tests/unit/users/user_repository_test.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/users/user_repository_test.py -v
```

Expected: FAIL — `UserRepository` does not exist yet.

- [ ] **Step 3: Implement UserRepository**

Create `app/users/user_repository.py`:

```python
import uuid

from sqlalchemy import select

from app.repositories import RepositorySession
from app.users.user_model import User


class UserRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.session.get(User, user_id)

    def find_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.scalar(stmt)

    def create(self, user: User) -> User:
        self.session.add(user)
        self.session.flush()
        return user
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/users/user_repository_test.py -v
```

Expected: PASS

- [ ] **Step 5: Write failing tests for UserOAuthAccountRepository**

Create `tests/unit/users/user_oauth_account_repository_test.py`:

```python
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
```

- [ ] **Step 6: Run tests to verify they fail**

```bash
uv run pytest tests/unit/users/user_oauth_account_repository_test.py -v
```

Expected: FAIL — `UserOAuthAccountRepository` does not exist yet.

- [ ] **Step 7: Implement UserOAuthAccountRepository**

Create `app/users/user_oauth_account_repository.py`:

```python
import uuid

from sqlalchemy import select

from app.repositories import RepositorySession
from app.users.user_oauth_account_model import UserOAuthAccount


class UserOAuthAccountRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_provider(self, provider: str, provider_id: str) -> UserOAuthAccount | None:
        stmt = select(UserOAuthAccount).where(
            UserOAuthAccount.provider == provider,
            UserOAuthAccount.provider_id == provider_id,
        )
        return self.session.scalar(stmt)

    def find_by_user_id(self, user_id: uuid.UUID) -> list[UserOAuthAccount]:
        stmt = select(UserOAuthAccount).where(UserOAuthAccount.user_id == user_id)
        return list(self.session.scalars(stmt))

    def create(self, account: UserOAuthAccount) -> UserOAuthAccount:
        self.session.add(account)
        self.session.flush()
        return account
```

- [ ] **Step 8: Run all user repository tests**

```bash
uv run pytest tests/unit/users/ -v
```

Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add app/users/ tests/unit/users/
git commit -m "feat: UserRepository and UserOAuthAccountRepository with tests"
```

---

### Task 7: Thread Repository (TDD)

**Files:**
- Create: `app/threads/thread_repository.py`
- Create: `tests/unit/threads/thread_repository_test.py`

- [ ] **Step 1: Write failing tests for ThreadRepository**

Create `tests/unit/threads/thread_repository_test.py`:

```python
import uuid

from app.threads.thread_model import Thread
from app.threads.thread_member_model import ThreadMember
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/threads/thread_repository_test.py -v
```

Expected: FAIL — `ThreadRepository` does not exist yet.

- [ ] **Step 3: Implement ThreadRepository**

Create `app/threads/thread_repository.py`:

```python
import uuid

from sqlalchemy import select

from app.repositories import RepositorySession
from app.threads.thread_member_model import ThreadMember
from app.threads.thread_model import Thread


class ThreadRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_id(self, thread_id: uuid.UUID) -> Thread | None:
        return self.session.get(Thread, thread_id)

    def create(self, thread: Thread) -> Thread:
        self.session.add(thread)
        self.session.flush()
        return thread

    def add_member(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> ThreadMember:
        member = ThreadMember(thread_id=thread_id, user_id=user_id)
        self.session.add(member)
        self.session.flush()
        return member

    def is_member(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        stmt = select(ThreadMember).where(
            ThreadMember.thread_id == thread_id,
            ThreadMember.user_id == user_id,
        )
        return self.session.scalar(stmt) is not None

    def list_members(self, thread_id: uuid.UUID) -> list[ThreadMember]:
        stmt = select(ThreadMember).where(ThreadMember.thread_id == thread_id)
        return list(self.session.scalars(stmt))

    def list_for_user(self, user_id: uuid.UUID) -> list[Thread]:
        stmt = (
            select(Thread)
            .join(ThreadMember, Thread.id == ThreadMember.thread_id)
            .where(ThreadMember.user_id == user_id)
        )
        return list(self.session.scalars(stmt))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/threads/ -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/threads/ tests/unit/threads/
git commit -m "feat: ThreadRepository with membership management and tests"
```

---

### Task 8: Message Repository (TDD)

**Files:**
- Create: `app/messages/message_repository.py`
- Create: `tests/unit/messages/message_repository_test.py`

- [ ] **Step 1: Write failing tests for MessageRepository**

Create `tests/unit/messages/message_repository_test.py`:

```python
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
    thread = ThreadRepository(db_session).create(
        Thread(name="general", created_by=user.id)
    )
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/messages/message_repository_test.py -v
```

Expected: FAIL — `MessageRepository` does not exist yet.

- [ ] **Step 3: Implement MessageRepository**

Create `app/messages/message_repository.py`:

```python
import uuid

from sqlalchemy import select

from app.messages.message_model import Message
from app.repositories import RepositorySession


class MessageRepository:
    def __init__(self, session: RepositorySession):
        self.session = session

    def find_by_id(self, message_id: uuid.UUID) -> Message | None:
        return self.session.get(Message, message_id)

    def create(self, message: Message) -> Message:
        self.session.add(message)
        self.session.flush()
        return message

    def list_by_thread(
        self, thread_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.thread_id == thread_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/messages/ -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/messages/ tests/unit/messages/
git commit -m "feat: MessageRepository with thread listing and tests"
```

---

### Task 9: OAuth Provider Abstraction and JWT Utilities

**Files:**
- Create: `app/auth/__init__.py`
- Create: `app/auth/oauth.py`
- Create: `app/auth/jwt.py`

- [ ] **Step 1: Create app/auth/__init__.py**

```python
```

- [ ] **Step 2: Create app/auth/oauth.py**

```python
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlencode

import requests

from app.exceptions import OAuthError


@dataclass
class OAuthUserInfo:
    email: str
    display_name: str
    avatar_url: str | None
    provider: str
    provider_id: str


class OAuthProvider(Protocol):
    def get_authorization_url(self, state: str) -> str: ...
    def exchange_code(self, code: str) -> OAuthUserInfo: ...


class GoogleOAuthProvider:
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> OAuthUserInfo:
        token_response = requests.post(
            self.TOKEN_URL,
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if token_response.status_code != 200:
            raise OAuthError(f"Google token exchange failed: {token_response.text}")

        access_token = token_response.json()["access_token"]

        userinfo_response = requests.get(
            self.USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if userinfo_response.status_code != 200:
            raise OAuthError(f"Google userinfo failed: {userinfo_response.text}")

        data = userinfo_response.json()
        return OAuthUserInfo(
            email=data["email"],
            display_name=data.get("name", data["email"]),
            avatar_url=data.get("picture"),
            provider="google",
            provider_id=data["sub"],
        )


class GitHubOAuthProvider:
    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    EMAILS_URL = "https://api.github.com/user/emails"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",
            "state": state,
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> OAuthUserInfo:
        token_response = requests.post(
            self.TOKEN_URL,
            data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        if token_response.status_code != 200:
            raise OAuthError(f"GitHub token exchange failed: {token_response.text}")

        access_token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        user_response = requests.get(self.USER_URL, headers=headers, timeout=10)
        if user_response.status_code != 200:
            raise OAuthError(f"GitHub user fetch failed: {user_response.text}")
        user_data = user_response.json()

        email = user_data.get("email")
        if not email:
            emails_response = requests.get(self.EMAILS_URL, headers=headers, timeout=10)
            if emails_response.status_code == 200:
                for entry in emails_response.json():
                    if entry.get("primary") and entry.get("verified"):
                        email = entry["email"]
                        break
        if not email:
            raise OAuthError("Could not retrieve email from GitHub")

        return OAuthUserInfo(
            email=email,
            display_name=user_data.get("name") or user_data["login"],
            avatar_url=user_data.get("avatar_url"),
            provider="github",
            provider_id=str(user_data["id"]),
        )


class FakeOAuthProvider:
    """Test fake — returns preconfigured user info without hitting any external service."""

    def __init__(self, user_info: OAuthUserInfo):
        self.user_info = user_info

    def get_authorization_url(self, state: str) -> str:
        return f"http://fake-oauth/authorize?state={state}"

    def exchange_code(self, code: str) -> OAuthUserInfo:
        return self.user_info
```

- [ ] **Step 3: Create app/auth/jwt.py**

```python
import uuid
from datetime import datetime, timedelta, timezone

import jwt as pyjwt


def encode_token(user_id: uuid.UUID, secret: str, expires_in: int = 86400) -> str:
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(seconds=expires_in),
    }
    return pyjwt.encode(payload, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> uuid.UUID:
    payload = pyjwt.decode(token, secret, algorithms=["HS256"])
    return uuid.UUID(payload["sub"])
```

- [ ] **Step 4: Commit**

```bash
git add app/auth/
git commit -m "feat: OAuth provider abstraction (Google, GitHub, Fake) and JWT utilities"
```

---

### Task 10: Auth Service (TDD)

**Files:**
- Create: `app/auth/auth_service.py`
- Create: `tests/unit/auth/auth_service_test.py`

- [ ] **Step 1: Write failing tests for AuthService**

Create `tests/unit/auth/auth_service_test.py`:

```python
import uuid

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/auth/auth_service_test.py -v
```

Expected: FAIL — `AuthService` does not exist yet.

- [ ] **Step 3: Implement AuthService**

Create `app/auth/auth_service.py`:

```python
from sqlalchemy.orm import Session

from app.auth.jwt import encode_token
from app.auth.oauth import OAuthProvider
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
        jwt_secret: str,
    ):
        self.provider = provider
        self.user_repo = user_repo
        self.oauth_account_repo = oauth_account_repo
        self.session = session
        self.jwt_secret = jwt_secret

    def login(self, code: str) -> tuple[str, User]:
        user_info = self.provider.exchange_code(code)

        existing_account = self.oauth_account_repo.find_by_provider(
            user_info.provider, user_info.provider_id
        )
        if existing_account:
            user = self.user_repo.find_by_id(existing_account.user_id)
            token = encode_token(user.id, self.jwt_secret)
            return token, user

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

        self.session.commit()
        token = encode_token(user.id, self.jwt_secret)
        return token, user
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/auth/auth_service_test.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/auth/auth_service.py tests/unit/auth/
git commit -m "feat: AuthService with user creation, email merging, OAuth account linking"
```

---

### Task 11: Thread Service (TDD)

**Files:**
- Create: `app/threads/thread_service.py`
- Create: `tests/unit/threads/thread_service_test.py`

- [ ] **Step 1: Write failing tests for ThreadService**

Create `tests/unit/threads/thread_service_test.py`:

```python
import uuid
from unittest.mock import MagicMock

import pytest

from app.exceptions import NotAMemberError, ThreadNotFoundError
from app.threads.thread_model import Thread
from app.threads.thread_member_model import ThreadMember
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/threads/thread_service_test.py -v
```

Expected: FAIL — `ThreadService` does not exist yet.

- [ ] **Step 3: Implement ThreadService**

Create `app/threads/thread_service.py`:

```python
import uuid

from sqlalchemy.orm import Session

from app.exceptions import AlreadyAMemberError, ThreadNotFoundError
from app.threads.thread_model import Thread
from app.threads.thread_repository import ThreadRepository


class ThreadService:
    def __init__(self, thread_repo: ThreadRepository, session: Session):
        self.thread_repo = thread_repo
        self.session = session

    def create_thread(self, name: str, user_id: uuid.UUID) -> Thread:
        thread = self.thread_repo.create(Thread(name=name, created_by=user_id))
        self.thread_repo.add_member(thread.id, user_id)
        self.session.commit()
        return thread

    def join_thread(self, thread_id: uuid.UUID, user_id: uuid.UUID) -> None:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        if self.thread_repo.is_member(thread_id, user_id):
            raise AlreadyAMemberError(user_id, thread_id)
        self.thread_repo.add_member(thread_id, user_id)
        self.session.commit()

    def list_threads(self, user_id: uuid.UUID) -> list[Thread]:
        return self.thread_repo.list_for_user(user_id)

    def get_thread(self, thread_id: uuid.UUID) -> Thread:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        return thread
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/threads/thread_service_test.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/threads/thread_service.py tests/unit/threads/thread_service_test.py
git commit -m "feat: ThreadService with create, join, list and tests"
```

---

### Task 12: Message Service (TDD)

**Files:**
- Create: `app/messages/message_service.py`
- Create: `tests/unit/messages/message_service_test.py`

- [ ] **Step 1: Write failing tests for MessageService**

Create `tests/unit/messages/message_service_test.py`:

```python
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
        service.send_message(
            user_id=uuid.uuid4(), thread_id=uuid.uuid4(), content="hello"
        )


def test_send_message_raises_when_not_a_member():
    thread_repo = MagicMock()
    thread_repo.find_by_id.return_value = Thread(
        name="general", created_by=uuid.uuid4()
    )
    thread_repo.is_member.return_value = False

    service = _make_service(thread_repo=thread_repo)
    with pytest.raises(NotAMemberError):
        service.send_message(
            user_id=uuid.uuid4(), thread_id=uuid.uuid4(), content="hello"
        )


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

    service = _make_service(
        message_repo=message_repo, thread_repo=thread_repo, session=session
    )
    result = service.send_message(
        user_id=user_id, thread_id=thread_id, content="hello"
    )

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

    thread_repo.find_by_id.return_value = Thread(
        name="general", created_by=uuid.uuid4()
    )
    expected = [MagicMock(), MagicMock()]
    message_repo.list_by_thread.return_value = expected

    service = _make_service(message_repo=message_repo, thread_repo=thread_repo)
    result = service.list_messages(thread_id=thread_id, limit=10)

    assert result == expected
    message_repo.list_by_thread.assert_called_once_with(thread_id, limit=10, offset=0)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/messages/message_service_test.py -v
```

Expected: FAIL — `MessageService` does not exist yet.

- [ ] **Step 3: Implement MessageService**

Create `app/messages/message_service.py`:

```python
import uuid

from sqlalchemy.orm import Session

from app.exceptions import NotAMemberError, ThreadNotFoundError
from app.messages.message_model import Message
from app.messages.message_repository import MessageRepository
from app.threads.thread_repository import ThreadRepository


class MessageService:
    def __init__(
        self,
        message_repo: MessageRepository,
        thread_repo: ThreadRepository,
        session: Session,
    ):
        self.message_repo = message_repo
        self.thread_repo = thread_repo
        self.session = session

    def send_message(
        self, user_id: uuid.UUID, thread_id: uuid.UUID, content: str
    ) -> Message:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        if not self.thread_repo.is_member(thread_id, user_id):
            raise NotAMemberError(user_id, thread_id)

        message = self.message_repo.create(
            Message(thread_id=thread_id, user_id=user_id, content=content)
        )
        self.session.commit()
        return message

    def list_messages(
        self, thread_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Message]:
        thread = self.thread_repo.find_by_id(thread_id)
        if not thread:
            raise ThreadNotFoundError(thread_id)
        return self.message_repo.list_by_thread(thread_id, limit=limit, offset=offset)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/messages/message_service_test.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/messages/message_service.py tests/unit/messages/message_service_test.py
git commit -m "feat: MessageService with send, list, membership checks and tests"
```

---

### Task 13: User Service (TDD)

**Files:**
- Create: `app/users/user_service.py`
- Create: `tests/unit/users/user_service_test.py`

- [ ] **Step 1: Write failing tests for UserService**

Create `tests/unit/users/user_service_test.py`:

```python
import uuid
from unittest.mock import MagicMock

import pytest

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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/unit/users/user_service_test.py -v
```

Expected: FAIL — `UserService` does not exist yet.

- [ ] **Step 3: Implement UserService**

Create `app/users/user_service.py`:

```python
import uuid

from app.exceptions import UserNotFoundError
from app.users.user_model import User
from app.users.user_repository import UserRepository


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    def get_me(self, user_id: uuid.UUID) -> User:
        return self.get_user(user_id)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/users/user_service_test.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/users/user_service.py tests/unit/users/user_service_test.py
git commit -m "feat: UserService with get_user, get_me and tests"
```

---

### Task 14: Dependency Factories and Auth Decorators

**Files:**
- Create: `app/dependencies.py`
- Create: `app/auth/decorators.py`

- [ ] **Step 1: Create app/dependencies.py**

```python
from flask import current_app

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
    session = session or db.session
    return UserService(user_repo=UserRepository(session))


def get_thread_service(session=None) -> ThreadService:
    session = session or db.session
    return ThreadService(
        thread_repo=ThreadRepository(session),
        session=session,
    )


def get_message_service(session=None) -> MessageService:
    session = session or db.session
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
    session = session or db.session
    return AuthService(
        provider=provider,
        user_repo=UserRepository(session),
        oauth_account_repo=UserOAuthAccountRepository(session),
        session=session,
        jwt_secret=current_app.config["JWT_SECRET"],
    )
```

- [ ] **Step 2: Create app/auth/decorators.py**

```python
import functools
import uuid

from flask import current_app, g, request
from flask_socketio import disconnect

from app.auth.jwt import decode_token


def _extract_user_id() -> uuid.UUID | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    try:
        return decode_token(token, current_app.config["JWT_SECRET"])
    except Exception:
        return None


def require_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user_id = _extract_user_id()
        if user_id is None:
            return {"error": "Unauthorized"}, 401
        g.current_user_id = user_id
        return f(*args, **kwargs)

    return decorated


def current_user_id() -> uuid.UUID:
    return g.current_user_id


def require_socket_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        user_id = _extract_user_id()
        if user_id is None:
            disconnect()
            return
        g.current_user_id = user_id
        return f(*args, **kwargs)

    return decorated
```

- [ ] **Step 3: Commit**

```bash
git add app/dependencies.py app/auth/decorators.py
git commit -m "feat: dependency factory functions and auth decorators"
```

---

### Task 15: Auth Routes + Integration Tests (TDD)

**Files:**
- Create: `app/auth/auth_routes.py`
- Create: `tests/integration/auth/auth_routes_test.py`
- Modify: `app/__init__.py`

- [ ] **Step 1: Write failing integration tests for auth routes**

Create `tests/integration/auth/auth_routes_test.py`:

```python
from app.auth.oauth import FakeOAuthProvider, OAuthUserInfo


def test_oauth_callback_creates_user_and_returns_jwt(app, client):
    fake_provider = FakeOAuthProvider(
        OAuthUserInfo(
            email="new@example.com",
            display_name="New User",
            avatar_url=None,
            provider="google",
            provider_id="g-999",
        )
    )
    app.config["_test_oauth_provider"] = fake_provider

    response = client.get("/auth/google/callback?code=fake-code&state=test")
    assert response.status_code == 200
    data = response.get_json()
    assert "token" in data
    assert data["user"]["email"] == "new@example.com"


def test_oauth_callback_returns_existing_user_on_second_login(app, client):
    fake_provider = FakeOAuthProvider(
        OAuthUserInfo(
            email="returning@example.com",
            display_name="Returning User",
            avatar_url=None,
            provider="google",
            provider_id="g-888",
        )
    )
    app.config["_test_oauth_provider"] = fake_provider

    response1 = client.get("/auth/google/callback?code=fake-code&state=test")
    response2 = client.get("/auth/google/callback?code=fake-code&state=test")

    data1 = response1.get_json()
    data2 = response2.get_json()
    assert data1["user"]["id"] == data2["user"]["id"]


def test_oauth_login_redirects(app, client):
    response = client.get("/auth/google/login")
    assert response.status_code == 302
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/integration/auth/auth_routes_test.py -v
```

Expected: FAIL — no routes registered.

- [ ] **Step 3: Implement auth routes**

Create `app/auth/auth_routes.py`:

```python
import secrets

from flask import Blueprint, current_app, redirect, request

from app.dependencies import get_auth_service, get_oauth_provider

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _serialize_user(user):
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
    }


@auth_bp.route("/<provider_name>/login")
def oauth_login(provider_name: str):
    provider = get_oauth_provider(provider_name)
    state = secrets.token_urlsafe(32)
    url = provider.get_authorization_url(state)
    return redirect(url)


@auth_bp.route("/<provider_name>/callback")
def oauth_callback(provider_name: str):
    code = request.args.get("code")
    if not code:
        return {"error": "Missing code parameter"}, 400

    test_provider = current_app.config.get("_test_oauth_provider")
    provider = test_provider or get_oauth_provider(provider_name)

    service = get_auth_service(provider=provider)
    token, user = service.login(code=code)

    return {"token": token, "user": _serialize_user(user)}
```

- [ ] **Step 4: Register blueprint in app factory**

Update `app/__init__.py`:

```python
from flask import Flask

from app.config import DevConfig
from app.extensions import db, migrate, socketio


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(config or DevConfig)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    with app.app_context():
        import app.users.user_model  # noqa: F401
        import app.users.user_oauth_account_model  # noqa: F401
        import app.threads.thread_model  # noqa: F401
        import app.threads.thread_member_model  # noqa: F401
        import app.messages.message_model  # noqa: F401

    from app.auth.auth_routes import auth_bp

    app.register_blueprint(auth_bp)

    return app
```

- [ ] **Step 5: Run integration tests**

```bash
uv run pytest tests/integration/auth/auth_routes_test.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/auth/auth_routes.py app/__init__.py tests/integration/auth/
git commit -m "feat: auth routes (OAuth login/callback) with integration tests"
```

---

### Task 16: Thread Routes + Integration Tests (TDD)

**Files:**
- Create: `app/threads/thread_routes.py`
- Create: `tests/integration/threads/thread_routes_test.py`
- Modify: `app/__init__.py`

- [ ] **Step 1: Write failing integration tests for thread routes**

Create `tests/integration/threads/thread_routes_test.py`:

```python
import uuid

from app.users.user_model import User
from app.users.user_repository import UserRepository


def _create_authenticated_user(db_session, make_auth_header, email="threads@example.com"):
    repo = UserRepository(db_session)
    user = repo.create(User(email=email, display_name="Thread Tester"))
    db_session.commit()
    headers = make_auth_header(user.id)
    return user, headers


def test_create_thread(app, client, db_session, make_auth_header):
    user, headers = _create_authenticated_user(db_session, make_auth_header)

    response = client.post(
        "/threads",
        json={"name": "general"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "general"
    assert data["created_by"] == str(user.id)


def test_create_thread_requires_auth(client):
    response = client.post("/threads", json={"name": "general"})
    assert response.status_code == 401


def test_list_threads(app, client, db_session, make_auth_header):
    user, headers = _create_authenticated_user(db_session, make_auth_header)

    client.post("/threads", json={"name": "thread-1"}, headers=headers)
    client.post("/threads", json={"name": "thread-2"}, headers=headers)

    response = client.get("/threads", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2


def test_join_thread(app, client, db_session, make_auth_header):
    user1, headers1 = _create_authenticated_user(
        db_session, make_auth_header, "creator@example.com"
    )
    user2, headers2 = _create_authenticated_user(
        db_session, make_auth_header, "joiner@example.com"
    )

    create_resp = client.post(
        "/threads", json={"name": "public"}, headers=headers1
    )
    thread_id = create_resp.get_json()["id"]

    join_resp = client.post(f"/threads/{thread_id}/join", headers=headers2)
    assert join_resp.status_code == 200
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/integration/threads/thread_routes_test.py -v
```

Expected: FAIL — no thread routes.

- [ ] **Step 3: Implement thread routes**

Create `app/threads/thread_routes.py`:

```python
from flask import Blueprint, request

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_thread_service
from app.exceptions import AlreadyAMemberError, ThreadNotFoundError

threads_bp = Blueprint("threads", __name__, url_prefix="/threads")


def _serialize_thread(thread):
    return {
        "id": str(thread.id),
        "name": thread.name,
        "created_by": str(thread.created_by),
        "created_at": thread.created_at.isoformat(),
    }


@threads_bp.route("", methods=["POST"])
@require_auth
def create_thread():
    data = request.get_json()
    service = get_thread_service()
    thread = service.create_thread(name=data["name"], user_id=current_user_id())
    return _serialize_thread(thread), 201


@threads_bp.route("", methods=["GET"])
@require_auth
def list_threads():
    service = get_thread_service()
    threads = service.list_threads(user_id=current_user_id())
    return [_serialize_thread(t) for t in threads]


@threads_bp.route("/<thread_id>/join", methods=["POST"])
@require_auth
def join_thread(thread_id: str):
    import uuid

    service = get_thread_service()
    try:
        service.join_thread(thread_id=uuid.UUID(thread_id), user_id=current_user_id())
    except ThreadNotFoundError:
        return {"error": "Thread not found"}, 404
    except AlreadyAMemberError:
        return {"error": "Already a member"}, 409
    return {"status": "joined"}
```

- [ ] **Step 4: Register blueprint in app factory**

Add to `app/__init__.py` after the auth blueprint registration:

```python
    from app.threads.thread_routes import threads_bp
    app.register_blueprint(threads_bp)
```

- [ ] **Step 5: Run integration tests**

```bash
uv run pytest tests/integration/threads/thread_routes_test.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/threads/thread_routes.py app/__init__.py tests/integration/threads/
git commit -m "feat: thread routes (create, list, join) with integration tests"
```

---

### Task 17: Message Routes + Integration Tests (TDD)

**Files:**
- Create: `app/messages/message_routes.py`
- Create: `tests/integration/messages/message_routes_test.py`
- Modify: `app/__init__.py`

- [ ] **Step 1: Write failing integration tests for message routes**

Create `tests/integration/messages/message_routes_test.py`:

```python
from app.users.user_model import User
from app.users.user_repository import UserRepository


def _setup_user_and_thread(client, db_session, make_auth_header):
    repo = UserRepository(db_session)
    user = repo.create(User(email="msg-route@example.com", display_name="Msg Tester"))
    db_session.commit()
    headers = make_auth_header(user.id)

    resp = client.post("/threads", json={"name": "chat"}, headers=headers)
    thread_id = resp.get_json()["id"]
    return user, headers, thread_id


def test_send_message(app, client, db_session, make_auth_header):
    user, headers, thread_id = _setup_user_and_thread(
        client, db_session, make_auth_header
    )

    response = client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "hello world"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["content"] == "hello world"
    assert data["user_id"] == str(user.id)


def test_send_message_requires_membership(app, client, db_session, make_auth_header):
    _, headers1, thread_id = _setup_user_and_thread(
        client, db_session, make_auth_header
    )

    repo = UserRepository(db_session)
    outsider = repo.create(
        User(email="outsider@example.com", display_name="Outsider")
    )
    db_session.commit()
    headers2 = make_auth_header(outsider.id)

    response = client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "should fail"},
        headers=headers2,
    )
    assert response.status_code == 403


def test_list_messages(app, client, db_session, make_auth_header):
    user, headers, thread_id = _setup_user_and_thread(
        client, db_session, make_auth_header
    )

    client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "msg 1"},
        headers=headers,
    )
    client.post(
        f"/threads/{thread_id}/messages",
        json={"content": "msg 2"},
        headers=headers,
    )

    response = client.get(f"/threads/{thread_id}/messages", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]["content"] == "msg 1"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/integration/messages/message_routes_test.py -v
```

Expected: FAIL — no message routes.

- [ ] **Step 3: Implement message routes**

Create `app/messages/message_routes.py`:

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


@messages_bp.route("/threads/<thread_id>/messages", methods=["POST"])
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


@messages_bp.route("/threads/<thread_id>/messages", methods=["GET"])
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

- [ ] **Step 4: Register blueprint in app factory**

Add to `app/__init__.py`:

```python
    from app.messages.message_routes import messages_bp
    app.register_blueprint(messages_bp)
```

- [ ] **Step 5: Run integration tests**

```bash
uv run pytest tests/integration/messages/message_routes_test.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/messages/message_routes.py app/__init__.py tests/integration/messages/message_routes_test.py
git commit -m "feat: message routes (send, list) with integration tests"
```

---

### Task 18: User Routes + Integration Tests (TDD)

**Files:**
- Create: `app/users/user_routes.py`
- Create: `tests/integration/users/user_routes_test.py`
- Modify: `app/__init__.py`

- [ ] **Step 1: Write failing integration tests for user routes**

Create `tests/integration/users/user_routes_test.py`:

```python
from app.users.user_model import User
from app.users.user_repository import UserRepository


def test_get_me(app, client, db_session, make_auth_header):
    repo = UserRepository(db_session)
    user = repo.create(User(email="me@example.com", display_name="Me"))
    db_session.commit()
    headers = make_auth_header(user.id)

    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data["email"] == "me@example.com"
    assert data["display_name"] == "Me"


def test_get_me_requires_auth(client):
    response = client.get("/users/me")
    assert response.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/integration/users/user_routes_test.py -v
```

Expected: FAIL — no user routes.

- [ ] **Step 3: Implement user routes**

Create `app/users/user_routes.py`:

```python
from flask import Blueprint

from app.auth.decorators import current_user_id, require_auth
from app.dependencies import get_user_service
from app.exceptions import UserNotFoundError

users_bp = Blueprint("users", __name__, url_prefix="/users")


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

- [ ] **Step 4: Register blueprint in app factory**

Add to `app/__init__.py`:

```python
    from app.users.user_routes import users_bp
    app.register_blueprint(users_bp)
```

- [ ] **Step 5: Run integration tests**

```bash
uv run pytest tests/integration/users/user_routes_test.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/users/user_routes.py app/__init__.py tests/integration/users/
git commit -m "feat: user routes (GET /users/me) with integration tests"
```

---

### Task 19: WebSocket Events + Integration Tests (TDD)

**Files:**
- Create: `app/messages/message_events.py`
- Create: `tests/integration/messages/message_events_test.py`
- Modify: `app/__init__.py`

- [ ] **Step 1: Write failing integration tests for websocket events**

Create `tests/integration/messages/message_events_test.py`:

```python
import uuid

from app.extensions import socketio
from app.users.user_model import User
from app.users.user_repository import UserRepository
from app.threads.thread_model import Thread
from app.threads.thread_repository import ThreadRepository


def _setup(db_session):
    user_repo = UserRepository(db_session)
    thread_repo = ThreadRepository(db_session)

    user = user_repo.create(User(email="ws@example.com", display_name="WS Tester"))
    thread = thread_repo.create(Thread(name="ws-thread", created_by=user.id))
    thread_repo.add_member(thread.id, user.id)
    db_session.commit()
    return user, thread


def test_join_thread_event(app, db_session, make_auth_header):
    user, thread = _setup(db_session)
    headers = make_auth_header(user.id)

    ws_client = socketio.test_client(app, headers=headers)
    assert ws_client.is_connected()

    ws_client.emit("join_thread", {"thread_id": str(thread.id)})
    received = ws_client.get_received()

    assert any(msg["name"] == "thread_joined" for msg in received)
    ws_client.disconnect()


def test_send_message_event_broadcasts(app, db_session, make_auth_header):
    user, thread = _setup(db_session)
    headers = make_auth_header(user.id)

    ws_client = socketio.test_client(app, headers=headers)
    ws_client.emit("join_thread", {"thread_id": str(thread.id)})
    ws_client.get_received()  # clear join messages

    ws_client.emit("send_message", {
        "thread_id": str(thread.id),
        "content": "hello via websocket",
    })
    received = ws_client.get_received()

    new_message_events = [m for m in received if m["name"] == "new_message"]
    assert len(new_message_events) == 1
    assert new_message_events[0]["args"][0]["content"] == "hello via websocket"
    ws_client.disconnect()


def test_send_message_event_rejected_without_auth(app):
    ws_client = socketio.test_client(app)
    assert not ws_client.is_connected()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/integration/messages/message_events_test.py -v
```

Expected: FAIL — no event handlers registered.

- [ ] **Step 3: Implement message events**

Create `app/messages/message_events.py`:

```python
from flask import g, request, current_app
from flask_socketio import disconnect, emit, join_room

from app.auth.jwt import decode_token
from app.dependencies import get_message_service
from app.exceptions import NotAMemberError, ThreadNotFoundError
from app.extensions import socketio

import uuid


@socketio.on("connect")
def handle_connect(auth=None):
    token = request.headers.get("Authorization", "")
    if not token.startswith("Bearer "):
        return False
    try:
        user_id = decode_token(token[7:], current_app.config["JWT_SECRET"])
        g.current_user_id = user_id
    except Exception:
        return False


@socketio.on("join_thread")
def handle_join_thread(data):
    thread_id = data["thread_id"]
    join_room(thread_id)
    emit("thread_joined", {"thread_id": thread_id})


@socketio.on("send_message")
def handle_send_message(data):
    service = get_message_service()
    try:
        message = service.send_message(
            user_id=g.current_user_id,
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

- [ ] **Step 4: Register events in app factory**

Add to `app/__init__.py` inside `create_app`, after blueprint registrations:

```python
    import app.messages.message_events  # noqa: F401
```

- [ ] **Step 5: Run integration tests**

```bash
uv run pytest tests/integration/messages/message_events_test.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/messages/message_events.py app/__init__.py tests/integration/messages/message_events_test.py
git commit -m "feat: WebSocket events (connect, join_thread, send_message) with integration tests"
```

---

### Task 20: E2E Test

**Files:**
- Create: `tests/e2e/chat_flow_test.py`

- [ ] **Step 1: Write E2E test for full chat flow**

Create `tests/e2e/chat_flow_test.py`:

```python
"""
End-to-end test: full chat flow through REST and WebSocket.

1. Two users authenticate via OAuth
2. User 1 creates a thread
3. User 2 joins the thread
4. User 1 sends a message via WebSocket
5. User 2 receives the message via WebSocket
6. Messages are retrievable via REST
"""

from app.auth.oauth import FakeOAuthProvider, OAuthUserInfo
from app.extensions import socketio


def _login_user(app, client, email, display_name, provider_id):
    fake = FakeOAuthProvider(
        OAuthUserInfo(
            email=email,
            display_name=display_name,
            avatar_url=None,
            provider="google",
            provider_id=provider_id,
        )
    )
    app.config["_test_oauth_provider"] = fake
    response = client.get("/auth/google/callback?code=fake&state=test")
    data = response.get_json()
    return data["token"], data["user"]


def test_full_chat_flow(app, client):
    # Step 1: Two users authenticate
    token1, user1 = _login_user(app, client, "alice@example.com", "Alice", "g-alice")
    token2, user2 = _login_user(app, client, "bob@example.com", "Bob", "g-bob")

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Step 2: Alice creates a thread
    create_resp = client.post(
        "/threads", json={"name": "project-chat"}, headers=headers1
    )
    assert create_resp.status_code == 201
    thread_id = create_resp.get_json()["id"]

    # Step 3: Bob joins the thread
    join_resp = client.post(f"/threads/{thread_id}/join", headers=headers2)
    assert join_resp.status_code == 200

    # Step 4: Both connect via WebSocket and join the thread room
    ws1 = socketio.test_client(app, headers=headers1)
    ws2 = socketio.test_client(app, headers=headers2)

    assert ws1.is_connected()
    assert ws2.is_connected()

    ws1.emit("join_thread", {"thread_id": thread_id})
    ws2.emit("join_thread", {"thread_id": thread_id})
    ws1.get_received()  # clear
    ws2.get_received()  # clear

    # Step 5: Alice sends a message, Bob receives it
    ws1.emit("send_message", {"thread_id": thread_id, "content": "Hey Bob!"})

    bob_received = ws2.get_received()
    new_messages = [m for m in bob_received if m["name"] == "new_message"]
    assert len(new_messages) == 1
    assert new_messages[0]["args"][0]["content"] == "Hey Bob!"
    assert new_messages[0]["args"][0]["user_id"] == user1["id"]

    # Step 6: Messages retrievable via REST
    list_resp = client.get(f"/threads/{thread_id}/messages", headers=headers2)
    assert list_resp.status_code == 200
    messages = list_resp.get_json()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hey Bob!"

    ws1.disconnect()
    ws2.disconnect()
```

- [ ] **Step 2: Run the E2E test**

```bash
uv run pytest tests/e2e/chat_flow_test.py -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/e2e/
git commit -m "feat: E2E test covering full chat flow (auth, threads, websocket messaging)"
```

---

### Task 21: Run Full Test Suite and Final Cleanup

- [ ] **Step 1: Run all tests**

```bash
uv run pytest -v
```

Expected: All tests pass.

- [ ] **Step 2: Run linter**

```bash
uv run ruff check .
uv run ruff format --check .
```

Fix any issues found.

- [ ] **Step 3: Run type checker**

```bash
uv run ty check
```

Fix any type errors. In particular, verify that if you add `self.session.commit()` to any repository, ty reports an error because `RepositorySession` does not expose `commit()`.

- [ ] **Step 4: Delete the smoke test**

```bash
rm tests/unit/smoke_test.py
```

It served its purpose during infrastructure setup.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup, all tests passing, linter and type checker clean"
```

---

### Task 22: Verify Docker Build

- [ ] **Step 1: Build the Docker image**

```bash
docker build -t flask-example .
```

Expected: Build succeeds with layer caching working (dependency layer separate from source layer).

- [ ] **Step 2: Run with Docker Compose**

```bash
docker compose up -d
```

- [ ] **Step 3: Verify the app starts**

```bash
docker compose logs app
```

Expected: Gunicorn starts and listens on port 5000.

- [ ] **Step 4: Tear down**

```bash
docker compose down
```

- [ ] **Step 5: Commit any Docker fixes if needed**

```bash
git add Dockerfile docker-compose.yml
git commit -m "fix: finalize Docker build configuration"
```
