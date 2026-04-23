# The Flask Backend Manifesto — Design Spec

A public-facing HTML page presenting a set of convictions about writing backend Flask code that is testable, maintainable, and honest. Inspired by the Agile Manifesto in format and intent. Published via GitHub Pages and linked to this repository as a working example.

## Goal

Share a set of hard-won principles broadly — for developers new to Flask and experienced ones looking to improve their architecture. The page should be something worth bookmarking and sharing.

## The Manifesto

Six "We believe" statements in conviction-first format:

1. *We believe entry points should direct traffic, not conduct business.*
2. *We believe a rule only enforced by convention is a rule waiting to be broken.*
3. *We believe control over your dependencies is control over your tests.*
4. *We believe the measure of a test suite is the confidence it instills, not the lines it covers.*
5. *We believe difficult tests are a design problem, not a testing problem.*
6. *We believe simplicity that anyone can follow beats cleverness that only you can maintain.*

The arc moves from structure (1) → enforcement (2) → dependencies (3) → testing philosophy (4–5) → philosophy (6).

## Page Layout

Two-column split, single HTML file with embedded CSS and JS. No build step required — deployable directly to GitHub Pages.

### Header
- Title: "The Flask Backend Manifesto"
- Tagline: "Principles for backend Flask code that lasts"
- Link to this repository as a working example of the principles in practice

### Left Sidebar (fixed)
- Numbered list of all 6 "We believe" statements
- Each statement is a clickable anchor link jumping to its section on the right
- Active statement highlighted as the user scrolls (intersection observer)
- Fixed position so the full manifesto is always visible while reading breakdowns

### Right Column (scrollable)
A sticky two-line header sits at the top of the right column:
- Line 1: **"We believe"** — static, always visible, same size and weight
- Line 2: *the rest of the active statement* — updates dynamically as the user scrolls between sections, driven by the same intersection observer that highlights the sidebar

This prevents layout jank from varying statement lengths and gives the page a consistent visual anchor while reading. Below the sticky header, each section contains:
- **Why** — 2–4 sentences explaining the conviction and what goes wrong when ignored
- **What it unlocks** — a before/after code block showing the anti-pattern vs. the better approach

### Footer
- Author name (Ross Reicks)
- Date published
- Link to the repository

### Mobile
Sidebar collapses. Manifesto statements appear stacked above the breakdowns as a block, then each breakdown follows in order.

## Visual Design

- Dark background (`#0f0f0f`), off-white text (`#e8e6e1`)
- Single amber accent color (`#d4a847`) for headings, highlights, and active sidebar state
- Clean sans-serif (system font stack) for prose
- Monospace for code blocks, with subtle dark background (`#1a1a1a`) and amber syntax hints
- No external dependencies — no CDN fonts, no frameworks, no JS libraries

## Principle Breakdowns

### 1. Entry points should direct traffic, not conduct business

**Why:** When a route handler validates input, calls a service, *and* makes business decisions, it becomes impossible to test the business logic in isolation. It also becomes impossible to add a second entry point (WebSocket, CLI, background job) that shares the same logic. Entry points are transport — they should hand off immediately.

**Anti-pattern:**
```python
@app.route("/threads/<thread_id>/messages", methods=["POST"])
def create_message(thread_id):
    data = request.json
    thread = db.session.get(Thread, thread_id)
    if thread is None:
        return jsonify({"error": "not found"}), 404
    if current_user.id not in [m.user_id for m in thread.members]:
        return jsonify({"error": "forbidden"}), 403
    message = Message(thread_id=thread_id, user_id=current_user.id, body=data["body"])
    db.session.add(message)
    db.session.commit()
    return jsonify(message.to_dict()), 201
```

**Better:**
```python
# The handler owns HTTP concerns. The service owns decisions.
@bp.route("/threads/<thread_id>/messages", methods=["POST"])
@require_auth
def create_message(thread_id):
    data = request.json
    service = get_message_service()
    try:
        message = service.create_message(
            thread_id=thread_id,
            user_id=g.current_user.id,
            body=data["body"],
        )
    except ThreadNotFound:
        return jsonify({"error": "not found"}), 404
    except NotThreadMember:
        return jsonify({"error": "forbidden"}), 403
    return jsonify(message.to_dict()), 201
```

---

### 2. A rule only enforced by convention is a rule waiting to be broken

**Why:** Architecture decisions documented in a README are forgotten. Decisions enforced by the type checker are impossible to violate without the build failing. The most important constraint in this codebase — that repositories never call `commit()` — is enforced by the `RepositorySession` protocol, not by asking nicely. Make your tools do the work.

**Anti-pattern:**
```python
# "Don't call commit() in repositories" — documented in the README
class MessageRepository:
    def save(self, message: Message) -> None:
        self.session.add(message)
        self.session.commit()  # oops — someone forgot the rule
```

**Better:**
```python
class RepositorySession(Protocol):
    """A session that cannot commit — only services own that boundary."""
    def add(self, instance: object) -> None: ...
    def get(self, entity: type, ident: object) -> Any: ...

class MessageRepository:
    def __init__(self, session: RepositorySession) -> None:
        self.session = session

    def save(self, message: Message) -> None:
        self.session.add(message)
        # session.commit() is not on the Protocol — ty will catch this at check time
```

---

### 3. Control over your dependencies is control over your tests

**Why:** When a service calls `datetime.now()` directly, you cannot write a deterministic test for expiry logic — the answer changes every second. When the clock is injected, you hand the test a fixed point in time and the behavior becomes predictable. This principle applies to anything external: time, randomness, email, HTTP. If you can inject it, you can control it.

**Anti-pattern:**
```python
# Time is hardwired — you cannot control it in tests
class TokenService:
    def is_expired(self, token: Token) -> bool:
        return token.expires_at < datetime.now()
```

**Better:**
```python
# Clock is injected — tests own time exactly
from collections.abc import Callable

class TokenService:
    def __init__(self, clock: Callable[[], datetime] = datetime.now) -> None:
        self.clock = clock

    def is_expired(self, token: Token) -> bool:
        return token.expires_at < self.clock()

# In tests:
fixed_time = datetime(2026, 6, 1, 12, 0, 0)
service = TokenService(clock=lambda: fixed_time)

token = Token(expires_at=fixed_time - timedelta(seconds=1))
assert service.is_expired(token) is True
```

---

### 4. The measure of a test suite is the confidence it instills, not the lines it covers

**Why:** A line of code being executed in a test is not the same as that line being verified. Coverage tools count executions, not assertions. A test that calls a function and checks that it returns "something" covers the line — and proves nothing. Confidence comes from asserting the right thing, not from making the test runner go green.

**Anti-pattern:**
```python
# 100% coverage — and zero confidence
def test_create_message():
    repo = FakeMessageRepository()
    service = MessageService(message_repo=repo, thread_repo=FakeThreadRepository())
    result = service.create_message(thread_id="t1", user_id="u1", body="hello")
    assert result is not None  # line executed, coverage satisfied, nothing verified
```

**Better:**
```python
# Asserts the things that actually matter
def test_create_message():
    repo = FakeMessageRepository()
    service = MessageService(message_repo=repo, thread_repo=FakeThreadRepository())
    message = service.create_message(thread_id="t1", user_id="u1", body="hello")
    assert message.body == "hello"
    assert message.thread_id == "t1"
    assert repo.saved[-1] is message  # proves it was actually persisted
```

---

### 5. Difficult tests are a design problem, not a testing problem

**Why:** When a test requires ten lines of setup, three patches, and two mock objects just to assert one thing, the problem is not the test — it is what the test is pointing at. Hard-to-test code is hard to reason about, hard to change, and hard to trust. Treat test pain as a design signal. If you cannot test it simply, simplify it.

**Anti-pattern:**
```python
# Ten lines of setup to test one assertion — the code is doing too much
def test_create_message():
    with patch("app.messages.message_routes.db") as mock_db:
        with patch("app.messages.message_routes.current_user") as mock_user:
            with patch("app.messages.message_routes.Thread") as mock_thread:
                mock_user.id = "user-1"
                mock_thread.query.get.return_value = MagicMock(members=[...])
                ...
```

**Better:**
```python
# One line of setup — the service takes what it needs, nothing more
def test_create_message():
    repo = FakeMessageRepository()
    service = MessageService(message_repo=repo, thread_repo=FakeThreadRepository())
    message = service.create_message(thread_id="t1", user_id="u1", body="hello")
    assert repo.saved[-1] == message
```

---

### 6. Simplicity that anyone can follow beats cleverness that only you can maintain

**Why:** Decorator-based dependency injection, metaclass magic, and dynamic route registration are impressive — right up until you need to debug them at 2am or onboard someone who has never seen the pattern before. The explicit call is slower to write once and faster to understand forever. Write for the reader, not the author.

**Anti-pattern:**
```python
# Impressive. Opaque.
@inject
@require_auth
@validate(MessageSchema)
def create_message(thread_id, data: MessageSchema, service: MessageService):
    return service.create_message(...)
```

**Better:**
```python
# Obvious. Traceable. Boring in the best way.
@bp.route("/threads/<thread_id>/messages", methods=["POST"])
@require_auth
def create_message(thread_id):
    data = request.json
    service = get_message_service()
    try:
        message = service.create_message(
            thread_id=thread_id,
            user_id=g.current_user.id,
            body=data["body"],
        )
    except ThreadNotFound:
        return jsonify({"error": "not found"}), 404
    except NotThreadMember:
        return jsonify({"error": "forbidden"}), 403
    return jsonify(message.to_dict()), 201
# Every dependency call is visible. No framework knowledge required to read this.
```

## Deployment

Single `index.html` file in a `/docs` or `/manifesto` directory at the repo root, or a dedicated `gh-pages` branch. GitHub Pages configured to serve from that location. No build step, no CI required.

## Out of Scope

- Backend API to serve the page
- Any frontend framework or build toolchain
- CMS or editable content layer
- Comments or interactivity beyond scroll-linked sidebar highlighting
