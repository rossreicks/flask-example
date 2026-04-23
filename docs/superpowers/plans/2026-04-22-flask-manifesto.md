# Flask Backend Manifesto — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a single-file HTML manifesto page presenting six Flask backend principles, with a two-column layout, dynamic sticky header, scroll-linked sidebar, and GitHub Pages deployment.

**Architecture:** One self-contained `manifesto/index.html` file — no build step, no framework, no CDN. Embedded CSS and JS. GitHub Pages serves it from the repo root.

**Tech Stack:** HTML5, CSS (custom properties, CSS Grid/Flexbox), vanilla JS (IntersectionObserver API)

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `manifesto/index.html` | Create | The complete manifesto page |

---

## Task 1: HTML skeleton, CSS foundation, and dark theme

**Files:**
- Create: `manifesto/index.html`

- [ ] **Step 1: Create `manifesto/index.html` with the full HTML skeleton**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>The Flask Backend Manifesto</title>
  <style>
    :root {
      --bg: #0f0f0f;
      --text: #e8e6e1;
      --accent: #d4a847;
      --muted: #888;
      --subtle: #bbb;
      --border: #222;
      --code-bg: #1a1a1a;
      --sidebar-width: 340px;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      font-size: 16px;
      line-height: 1.7;
    }

    a { color: var(--accent); text-decoration: none; }
    a:hover { text-decoration: underline; }

    /* ── Header ── */
    .site-header {
      padding: 3rem 4rem;
      border-bottom: 1px solid var(--border);
    }

    .site-header h1 {
      font-size: 2.5rem;
      font-weight: 800;
      color: var(--accent);
      letter-spacing: -0.02em;
    }

    .site-header .tagline {
      margin-top: 0.5rem;
      color: var(--muted);
      font-size: 1.1rem;
    }

    .site-header .repo-link {
      display: inline-block;
      margin-top: 1rem;
      font-size: 0.875rem;
    }

    /* ── Layout ── */
    .layout {
      display: flex;
      min-height: calc(100vh - 160px);
    }

    /* ── Sidebar ── */
    .sidebar {
      width: var(--sidebar-width);
      flex-shrink: 0;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      padding: 2.5rem 2rem;
      border-right: 1px solid var(--border);
    }

    .sidebar-label {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--muted);
      margin-bottom: 1.5rem;
    }

    .sidebar ol {
      list-style: none;
      counter-reset: principle;
    }

    .sidebar li {
      counter-increment: principle;
      display: flex;
      gap: 0.75rem;
      align-items: flex-start;
      margin-bottom: 1.75rem;
    }

    .sidebar li::before {
      content: counter(principle);
      color: var(--accent);
      font-size: 0.7rem;
      font-weight: 700;
      padding-top: 0.3rem;
      flex-shrink: 0;
      width: 1rem;
    }

    .sidebar a {
      color: #555;
      font-size: 0.85rem;
      line-height: 1.55;
      transition: color 0.15s ease;
    }

    .sidebar a:hover { color: var(--text); text-decoration: none; }
    .sidebar a.active { color: var(--accent); }

    /* ── Right column ── */
    .content { flex: 1; min-width: 0; }

    /* ── Sticky header ── */
    .sticky-header {
      position: sticky;
      top: 0;
      z-index: 10;
      background: var(--bg);
      border-bottom: 1px solid var(--border);
      padding: 1.25rem 4rem;
    }

    .we-believe {
      display: block;
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--accent);
      font-weight: 700;
    }

    .active-statement {
      display: block;
      font-size: 1.15rem;
      font-style: italic;
      color: var(--text);
      margin-top: 0.3rem;
    }

    /* ── Principle sections ── */
    .principle {
      padding: 4rem;
      border-bottom: 1px solid #111;
    }

    .principle-why-label {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.15em;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 0.75rem;
    }

    .principle-why {
      max-width: 68ch;
      color: var(--subtle);
      margin-bottom: 2.5rem;
    }

    /* ── Code blocks ── */
    .code-pair {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }

    .code-block h3 {
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-bottom: 0.5rem;
      font-weight: 700;
    }

    .code-block.anti h3 { color: #c0392b; }
    .code-block.better h3 { color: #27ae60; }

    pre {
      background: var(--code-bg);
      border-radius: 6px;
      padding: 1.25rem;
      overflow-x: auto;
      font-size: 0.78rem;
      line-height: 1.65;
      font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
      height: 100%;
    }

    code { color: var(--text); }

    /* Amber tint for comments in code */
    .comment { color: var(--accent); opacity: 0.75; font-style: italic; }

    /* ── Footer ── */
    footer {
      padding: 2rem 4rem;
      border-top: 1px solid var(--border);
      color: #444;
      font-size: 0.85rem;
    }

    /* ── Mobile ── */
    @media (max-width: 800px) {
      .site-header { padding: 2rem 1.5rem; }
      .site-header h1 { font-size: 1.75rem; }

      .layout { flex-direction: column; }

      .sidebar {
        position: static;
        height: auto;
        width: 100%;
        border-right: none;
        border-bottom: 1px solid var(--border);
        padding: 2rem 1.5rem;
      }

      .sticky-header { padding: 1rem 1.5rem; }
      .principle { padding: 2rem 1.5rem; }
      .code-pair { grid-template-columns: 1fr; }
      footer { padding: 1.5rem; }
    }
  </style>
</head>
<body>

  <header class="site-header">
    <h1>The Flask Backend Manifesto</h1>
    <p class="tagline">Principles for backend Flask code that lasts</p>
    <a class="repo-link" href="https://github.com/rossreicks/flask-example">
      View the working example →
    </a>
  </header>

  <div class="layout">

    <aside class="sidebar">
      <p class="sidebar-label">We believe</p>
      <ol id="sidebar-nav">
        <li><a href="#principle-1">entry points should direct traffic, not conduct business.</a></li>
        <li><a href="#principle-2">a rule only enforced by convention is a rule waiting to be broken.</a></li>
        <li><a href="#principle-3">control over your dependencies is control over your tests.</a></li>
        <li><a href="#principle-4">the measure of a test suite is the confidence it instills, not the lines it covers.</a></li>
        <li><a href="#principle-5">difficult tests are a design problem, not a testing problem.</a></li>
        <li><a href="#principle-6">simplicity that anyone can follow beats cleverness that only you can maintain.</a></li>
      </ol>
    </aside>

    <main class="content">

      <div class="sticky-header">
        <span class="we-believe">We believe</span>
        <span class="active-statement" id="active-statement">
          entry points should direct traffic, not conduct business.
        </span>
      </div>

      <!-- Principle 1 -->
      <section
        id="principle-1"
        class="principle"
        data-statement="entry points should direct traffic, not conduct business."
      >
        <p class="principle-why-label">Why</p>
        <p class="principle-why">
          When a route handler validates input, calls a service, <em>and</em> makes business
          decisions, it becomes impossible to test the business logic in isolation. It also
          becomes impossible to add a second entry point — a WebSocket handler, a CLI command,
          a background job — that shares the same logic. Entry points are transport.
          They should hand off immediately.
        </p>
        <div class="code-pair">
          <div class="code-block anti">
            <h3>Anti-pattern</h3>
            <pre><code>@app.route("/threads/&lt;thread_id&gt;/messages",
           methods=["POST"])
def create_message(thread_id):
    data = request.json
    thread = db.session.get(Thread, thread_id)
    if thread is None:
        return jsonify({"error": "not found"}), 404
    if current_user.id not in [
        m.user_id for m in thread.members
    ]:
        return jsonify({"error": "forbidden"}), 403
    message = Message(
        thread_id=thread_id,
        user_id=current_user.id,
        body=data["body"],
    )
    db.session.add(message)
    db.session.commit()
    return jsonify(message.to_dict()), 201</code></pre>
          </div>
          <div class="code-block better">
            <h3>Better</h3>
            <pre><code><span class="comment"># The handler owns HTTP concerns.
# The service owns decisions.</span>
@bp.route("/threads/&lt;thread_id&gt;/messages",
          methods=["POST"])
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
    return jsonify(message.to_dict()), 201</code></pre>
          </div>
        </div>
      </section>

      <!-- Principle 2 -->
      <section
        id="principle-2"
        class="principle"
        data-statement="a rule only enforced by convention is a rule waiting to be broken."
      >
        <p class="principle-why-label">Why</p>
        <p class="principle-why">
          Architecture decisions documented in a README are forgotten. Decisions enforced
          by the type checker are impossible to violate without the build failing. The most
          important constraint in this codebase — that repositories never call
          <code>commit()</code> — is enforced by the <code>RepositorySession</code> protocol,
          not by asking nicely. Make your tools do the work.
        </p>
        <div class="code-pair">
          <div class="code-block anti">
            <h3>Anti-pattern</h3>
            <pre><code><span class="comment"># "Don't call commit() in repositories"
# — documented in the README</span>
class MessageRepository:
    def save(self, message: Message) -> None:
        self.session.add(message)
        self.session.commit()
        <span class="comment"># oops — someone forgot the rule</span></code></pre>
          </div>
          <div class="code-block better">
            <h3>Better</h3>
            <pre><code>class RepositorySession(Protocol):
    def add(self, instance: object) -> None: ...
    def get(self, entity: type,
            ident: object) -> Any: ...
    <span class="comment"># commit() is intentionally absent</span>

class MessageRepository:
    def __init__(
        self, session: RepositorySession
    ) -> None:
        self.session = session

    def save(self, message: Message) -> None:
        self.session.add(message)
        <span class="comment"># session.commit() does not exist on
        # the Protocol — ty catches it at
        # check time, not runtime</span></code></pre>
          </div>
        </div>
      </section>

      <!-- Principle 3 -->
      <section
        id="principle-3"
        class="principle"
        data-statement="control over your dependencies is control over your tests."
      >
        <p class="principle-why-label">Why</p>
        <p class="principle-why">
          When a service calls <code>datetime.now()</code> directly, you cannot write a
          deterministic test for expiry logic — the answer changes every second. When the
          clock is injected, you hand the test a fixed point in time and the behavior becomes
          predictable. This applies to anything external: time, randomness, email, HTTP.
          If you can inject it, you can control it.
        </p>
        <div class="code-pair">
          <div class="code-block anti">
            <h3>Anti-pattern</h3>
            <pre><code><span class="comment"># Time is hardwired — you cannot
# control it in tests</span>
class TokenService:
    def is_expired(
        self, token: Token
    ) -> bool:
        return token.expires_at &lt; datetime.now()</code></pre>
          </div>
          <div class="code-block better">
            <h3>Better</h3>
            <pre><code><span class="comment"># Clock is injected — tests own time exactly</span>
from collections.abc import Callable

class TokenService:
    def __init__(
        self,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.clock = clock

    def is_expired(self, token: Token) -> bool:
        return token.expires_at &lt; self.clock()

<span class="comment"># In tests:</span>
fixed = datetime(2026, 6, 1, 12, 0, 0)
service = TokenService(clock=lambda: fixed)
token = Token(expires_at=fixed - timedelta(seconds=1))
assert service.is_expired(token) is True</code></pre>
          </div>
        </div>
      </section>

      <!-- Principle 4 -->
      <section
        id="principle-4"
        class="principle"
        data-statement="the measure of a test suite is the confidence it instills, not the lines it covers."
      >
        <p class="principle-why-label">Why</p>
        <p class="principle-why">
          A line of code being executed in a test is not the same as that line being verified.
          Coverage tools count executions, not assertions. A test that calls a function and
          checks that it returns "something" covers the line — and proves nothing. Confidence
          comes from asserting the right thing, not from making the test runner go green.
        </p>
        <div class="code-pair">
          <div class="code-block anti">
            <h3>Anti-pattern</h3>
            <pre><code><span class="comment"># 100% coverage — and zero confidence</span>
def test_create_message():
    repo = FakeMessageRepository()
    service = MessageService(
        message_repo=repo,
        thread_repo=FakeThreadRepository(),
    )
    result = service.create_message(
        thread_id="t1", user_id="u1", body="hello"
    )
    assert result is not None
    <span class="comment"># line executed, coverage satisfied,
    # nothing verified</span></code></pre>
          </div>
          <div class="code-block better">
            <h3>Better</h3>
            <pre><code><span class="comment"># Asserts the things that actually matter</span>
def test_create_message():
    repo = FakeMessageRepository()
    service = MessageService(
        message_repo=repo,
        thread_repo=FakeThreadRepository(),
    )
    message = service.create_message(
        thread_id="t1", user_id="u1", body="hello"
    )
    assert message.body == "hello"
    assert message.thread_id == "t1"
    assert repo.saved[-1] is message
    <span class="comment"># proves it was actually persisted</span></code></pre>
          </div>
        </div>
      </section>

      <!-- Principle 5 -->
      <section
        id="principle-5"
        class="principle"
        data-statement="difficult tests are a design problem, not a testing problem."
      >
        <p class="principle-why-label">Why</p>
        <p class="principle-why">
          When a test requires ten lines of setup, three patches, and two mock objects just
          to assert one thing, the problem is not the test — it is what the test is pointing
          at. Hard-to-test code is hard to reason about, hard to change, and hard to trust.
          Treat test pain as a design signal. If you cannot test it simply, simplify it.
        </p>
        <div class="code-pair">
          <div class="code-block anti">
            <h3>Anti-pattern</h3>
            <pre><code><span class="comment"># Ten lines of setup to test one thing
# — the code is doing too much</span>
def test_create_message():
    with patch(
        "app.messages.message_routes.db"
    ) as mock_db:
        with patch(
            "app.messages.message_routes.current_user"
        ) as mock_user:
            with patch(
                "app.messages.message_routes.Thread"
            ) as mock_thread:
                mock_user.id = "user-1"
                mock_thread.query.get.return_value = (
                    MagicMock(members=[...])
                )
                ...</code></pre>
          </div>
          <div class="code-block better">
            <h3>Better</h3>
            <pre><code><span class="comment"># One line of setup — the service takes
# what it needs, nothing more</span>
def test_create_message():
    repo = FakeMessageRepository()
    service = MessageService(
        message_repo=repo,
        thread_repo=FakeThreadRepository(),
    )
    message = service.create_message(
        thread_id="t1", user_id="u1", body="hello"
    )
    assert repo.saved[-1] == message</code></pre>
          </div>
        </div>
      </section>

      <!-- Principle 6 -->
      <section
        id="principle-6"
        class="principle"
        data-statement="simplicity that anyone can follow beats cleverness that only you can maintain."
      >
        <p class="principle-why-label">Why</p>
        <p class="principle-why">
          Decorator-based dependency injection, metaclass magic, and dynamic route registration
          are impressive — right up until you need to debug them at 2am or hand the codebase
          to someone new. The explicit call is slower to write once and faster to understand
          forever. Write for the reader, not the author.
        </p>
        <div class="code-pair">
          <div class="code-block anti">
            <h3>Anti-pattern</h3>
            <pre><code><span class="comment"># Impressive. Opaque.</span>
@inject
@require_auth
@validate(MessageSchema)
def create_message(
    thread_id,
    data: MessageSchema,
    service: MessageService,
):
    return service.create_message(...)</code></pre>
          </div>
          <div class="code-block better">
            <h3>Better</h3>
            <pre><code><span class="comment"># Obvious. Traceable. Boring in the best way.</span>
@bp.route("/threads/&lt;thread_id&gt;/messages",
          methods=["POST"])
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
<span class="comment"># No framework knowledge required to read this.</span></code></pre>
          </div>
        </div>
      </section>

    </main>
  </div>

  <footer>
    By Ross Reicks &middot; April 2026 &middot;
    <a href="https://github.com/rossreicks/flask-example">github.com/rossreicks/flask-example</a>
  </footer>

  <script>
    const sections = document.querySelectorAll('.principle');
    const sidebarLinks = document.querySelectorAll('#sidebar-nav a');
    const activeStatement = document.getElementById('active-statement');

    function setActive(index) {
      const section = sections[index];
      if (!section) return;

      activeStatement.textContent = section.dataset.statement;

      sidebarLinks.forEach((link, i) => {
        link.classList.toggle('active', i === index);
      });
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const index = Array.from(sections).indexOf(entry.target);
            setActive(index);
          }
        });
      },
      { rootMargin: '-15% 0px -70% 0px' }
    );

    sections.forEach((section) => observer.observe(section));
    setActive(0);
  </script>

</body>
</html>
```

- [ ] **Step 2: Verify in browser**

Open `manifesto/index.html` directly in a browser (File → Open, or `open manifesto/index.html` on Mac).

Check:
- Dark background (`#0f0f0f`), amber headings (`#d4a847`)
- Two-column layout: sidebar on left, content on right
- All 6 "We believe" statements visible in sidebar
- Sticky header shows "We believe" + first statement
- All 6 principle sections with Why text and before/after code blocks visible
- Footer with name and repo link

- [ ] **Step 3: Verify scroll behavior**

Scroll slowly through the sections and confirm:
- The second line of the sticky header updates to the current section's statement
- The active sidebar link highlights in amber
- No layout jank or jump as header text changes

- [ ] **Step 4: Verify mobile layout**

Open DevTools (F12), toggle device toolbar (Cmd+Shift+M), select a 375px wide viewport.

Check:
- Sidebar appears above content, full width, not fixed
- Sticky header visible
- Code pairs stack vertically (one per row)
- No horizontal overflow

- [ ] **Step 5: Commit**

```bash
git add manifesto/index.html
git commit -m "feat: add Flask Backend Manifesto HTML page"
```

---

## Task 2: GitHub Pages configuration

**Files:**
- No new files — GitHub Pages is configured via the repository settings UI

- [ ] **Step 1: Push the branch to GitHub**

```bash
git push origin main
```

- [ ] **Step 2: Enable GitHub Pages in repository settings**

1. Go to `https://github.com/rossreicks/flask-example/settings/pages`
2. Under **Source**, select **Deploy from a branch**
3. Branch: `main`, Folder: `/ (root)`
4. Click **Save**

GitHub Pages will build and publish. The manifesto will be live at:
```
https://rossreicks.github.io/flask-example/manifesto/
```

- [ ] **Step 3: Verify the live page**

Open `https://rossreicks.github.io/flask-example/manifesto/` in a browser.

Check:
- Page loads with correct dark theme and amber accents
- Scroll behavior works (sticky header updates, sidebar highlights)
- "View the working example →" link goes to the correct GitHub repo
- Mobile layout works (resize or use DevTools)

---

## Self-Review

**Spec coverage:**

| Spec requirement | Task |
|-----------------|------|
| Six "We believe" statements | Task 1 — sidebar + section `data-statement` |
| Two-column layout (sidebar fixed, content scrollable) | Task 1 — CSS `.layout`, `.sidebar`, `.content` |
| Sticky two-line header (static "We believe" + dynamic statement) | Task 1 — `.sticky-header`, JS `setActive()` |
| Scroll-linked sidebar highlighting | Task 1 — IntersectionObserver, `.active` class |
| WHY section per principle | Task 1 — `.principle-why` paragraphs |
| Before/after code blocks per principle | Task 1 — `.code-pair` `.anti` + `.better` |
| Dark theme with amber accent | Task 1 — CSS custom properties |
| No external dependencies | Task 1 — no CDN links, no `<link>` stylesheets |
| Mobile responsive (sidebar collapses, code stacks) | Task 1 — `@media (max-width: 800px)` |
| Header with title, tagline, repo link | Task 1 — `.site-header` |
| Footer with name, date, repo link | Task 1 — `<footer>` |
| GitHub Pages deployment | Task 2 |

All spec requirements covered.

**Placeholder scan:** No TBDs, no TODOs, no "implement later". All six principles have complete WHY text and before/after code blocks.

**Type consistency:** Single file — no cross-file references to drift.
