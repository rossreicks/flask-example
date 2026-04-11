# Flask Chat Application — Design Spec

A Flask chat application (Slack-style) demonstrating clean architecture and testability. Targets both Flask newcomers learning good patterns and experienced developers looking to retrofit testability into their apps.

## Domain

Real-time chat with users, threads, and messages. REST API for CRUD operations, WebSocket (Flask-SocketIO) for real-time messaging. API-only — no frontend.

## Project Structure

Domain-based folder organization. Each domain module is self-contained with its model, repository, service, and routes.

```
flask-example/
├── app/
│   ├── __init__.py              # App factory (create_app)
│   ├── config.py                # Config classes (Dev, Test, Prod)
│   ├── extensions.py            # SQLAlchemy, SocketIO, Migrate instances
│   ├── dependencies.py          # Factory functions for building services
│   ├── auth/
│   │   ├── oauth.py             # OAuthProvider protocol + Google/GitHub implementations
│   │   ├── decorators.py        # @require_auth for routes, @require_socket_auth for events
│   │   ├── auth_service.py      # Login/link flow, JWT issuance
│   │   └── auth_routes.py       # OAuth login/callback endpoints
│   ├── users/
│   │   ├── user_model.py
│   │   ├── user_oauth_account_model.py
│   │   ├── user_repository.py
│   │   ├── user_service.py
│   │   └── user_routes.py
│   ├── threads/
│   │   ├── thread_model.py
│   │   ├── thread_member_model.py
│   │   ├── thread_repository.py
│   │   ├── thread_service.py
│   │   └── thread_routes.py
│   └── messages/
│       ├── message_model.py
│       ├── message_repository.py
│       ├── message_service.py
│       ├── message_routes.py
│       └── message_events.py    # SocketIO event handlers
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/
│   │   ├── users/
│   │   │   ├── user_repository_test.py
│   │   │   └── user_service_test.py
│   │   ├── threads/
│   │   │   ├── thread_repository_test.py
│   │   │   └── thread_service_test.py
│   │   ├── messages/
│   │   │   ├── message_repository_test.py
│   │   │   └── message_service_test.py
│   │   └── auth/
│   │       └── auth_service_test.py
│   ├── integration/
│   │   ├── users/
│   │   │   └── user_routes_test.py
│   │   ├── threads/
│   │   │   └── thread_routes_test.py
│   │   ├── messages/
│   │   │   ├── message_routes_test.py
│   │   │   └── message_events_test.py
│   │   └── auth/
│   │       └── auth_routes_test.py
│   └── e2e/
│       └── chat_flow_test.py
├── migrations/                  # Alembic migrations
├── Dockerfile
├── docker-compose.yml
├── lefthook.yml
├── pyproject.toml
└── Makefile
```

Test files use `*_test.py` suffix (Go-style convention), configured via pytest's `python_files` setting.

## Data Model

### User
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary key |
| email | String | Unique, not null |
| display_name | String | Not null |
| avatar_url | String | Nullable |
| created_at | DateTime | Not null, default now |

### UserOAuthAccount
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK → User, not null |
| provider | String | Not null ("google" or "github") |
| provider_id | String | Not null |
| created_at | DateTime | Not null, default now |

Unique constraint on (`provider`, `provider_id`).

Users are merged by email: if a user logs in with Google and later with GitHub using the same email, both OAuth accounts link to the same user.

### Thread
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary key |
| name | String | Not null |
| created_by | UUID | FK → User, not null |
| created_at | DateTime | Not null, default now |

### ThreadMember
| Column | Type | Constraints |
|--------|------|-------------|
| thread_id | UUID | FK → Thread, composite PK |
| user_id | UUID | FK → User, composite PK |
| joined_at | DateTime | Not null, default now |

### Message
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary key |
| thread_id | UUID | FK → Thread, not null |
| user_id | UUID | FK → User, not null |
| content | Text | Not null |
| created_at | DateTime | Not null, default now |

## Architecture

### Layered Architecture

Routes/Events (thin) → Services (business logic) → Repositories (data access) → Models

Each layer has a single responsibility. Dependencies flow downward only.

### Repository Layer

Repositories take a restricted SQLAlchemy session and provide data access methods. They return model instances and contain no business logic.

**Session protocol enforcement**: Repositories receive a `RepositorySession` protocol type that excludes `commit()` and `rollback()`. The ty type checker catches any attempt to commit inside a repository at type-check time.

```python
class RepositorySession(Protocol):
    def add(self, instance) -> None: ...
    def delete(self, instance) -> None: ...
    def get(self, entity, ident) -> Any: ...
    def execute(self, statement) -> Any: ...
    def flush(self) -> None: ...
    # commit() intentionally excluded
```

**Repositories do not commit.** The service layer owns transaction boundaries. This allows a service to call multiple repos in a single transaction and roll back on failure.

### Service Layer

Services contain business logic and own transaction boundaries. They receive repositories as constructor arguments.

- Services call `session.commit()` — they own the transaction
- Custom exceptions (e.g., `ThreadNotFoundError`, `NotAMemberError`) for error cases
- Services are transport-agnostic — they don't know about HTTP or SocketIO

### Dependency Injection

Factory functions build dependency graphs. No DI framework. Handlers call the factory explicitly.

```python
# app/dependencies.py
def get_message_service(session=None):
    session = session or db.session
    return MessageService(
        message_repo=MessageRepository(session),
        thread_repo=ThreadRepository(session),
        session=session,
    )
```

Routes and event handlers call `get_message_service()`. Tests call `get_message_service(session=test_session)` or pass mock repos directly to the service constructor.

### Routes and Event Handlers

Thin entry points. They validate input, call a service, and handle transport-specific responses (JSON for REST, emit for SocketIO). The same service method is used by both REST and WebSocket paths.

## OAuth Authentication

### Provider Abstraction

```python
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
```

Two implementations: `GoogleOAuthProvider` and `GitHubOAuthProvider`.

### Auth Flow

1. Client hits `GET /auth/{provider}/login` → redirects to provider's consent screen
2. Provider redirects back to `GET /auth/{provider}/callback?code=...`
3. Route calls `provider.exchange_code(code)` → gets `OAuthUserInfo`
4. `AuthService` finds or creates the user by email, links the OAuth account if new
5. Returns a JWT

JWT is used for both REST (`Authorization` header) and WebSocket (query param during handshake).

### Test Fake

```python
class FakeOAuthProvider:
    def __init__(self, user_info: OAuthUserInfo):
        self.user_info = user_info

    def get_authorization_url(self, state: str) -> str:
        return f"http://fake-oauth/authorize?state={state}"

    def exchange_code(self, code: str) -> OAuthUserInfo:
        return self.user_info
```

Swapped in via the dependency factory during tests.

## WebSocket Design

Flask-SocketIO with JWT authentication on the handshake.

### Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `join_thread` | Client → Server | Join a thread's room |
| `leave_thread` | Client → Server | Leave a thread's room |
| `send_message` | Client → Server | Send a message to a thread |
| `new_message` | Server → Client | Broadcast when a message is created |

Event handlers follow the same thin-handler pattern as routes: validate input, call the service, emit to the room.

## Testing Strategy

### Test Layers

**Unit tests** — fast, isolated
- Service tests: mock repositories, test business logic and error cases
- Auth tests: `FakeOAuthProvider`, verify login/link flow logic
- Repository tests: real Postgres via testcontainers, each test in a rolled-back transaction

**Integration tests** — real database, real HTTP/WebSocket
- Flask test client and Flask-SocketIO test client
- Full request through route → service → repo → database
- OAuth faked at the provider level via factory override

**E2E tests** — full app, real connections
- Full app with testcontainers Postgres
- Real SocketIO client, fake OAuth, complete chat flow
- Verifies the system works as a client would experience it

### Test Database

- `testcontainers` spins up a disposable Postgres container per test session
- Alembic migrations run once at session start
- Each test gets a transaction that rolls back for fast isolation

### Key Fixtures (conftest.py)

- `app` — creates the app with test config
- `db_session` — per-test transactional session that rolls back
- `test_client` — Flask test client
- `socketio_client` — Flask-SocketIO test client
- `authenticated_user` — creates a user and returns a valid JWT
- `fake_oauth_provider` — preconfigured `FakeOAuthProvider`

### Pytest Configuration

```toml
[tool.pytest.ini_options]
python_files = "*_test.py"
python_functions = "test_*"
```

## Tooling

- **uv** — dependency management and virtual environment
- **Ruff** — linting and formatting
- **ty** — type checking (enforces RepositorySession protocol)
- **Alembic** — database migrations
- **pytest** — test runner
- **testcontainers** — disposable Postgres for tests

## Docker

### Dockerfile

Multi-stage build with good layer caching:
1. Base stage — Python + system dependencies
2. Dependencies stage — uv install (cached unless pyproject.toml/uv.lock changes)
3. App stage — copy source code, set entrypoint

Source code changes don't trigger dependency reinstallation.

### Docker Compose

- `postgres` — PostgreSQL service with health check and data volume
- `app` — Flask application, depends on postgres, environment variables for config (database URL, OAuth credentials, JWT secret)

## Lefthook

Git hook management:

- **pre-commit**: `ruff format --check` + `ruff check`
- **pre-push**: `ty` type checking + `pytest` (unit tests only for speed)
