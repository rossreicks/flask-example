# React Frontend Design

**Date:** 2026-04-12
**Status:** Approved

## Overview

Add a React + Vite frontend to the existing Flask chat application using the Inertia.js protocol via flask-inertia. Flask serves both the REST API and the built React assets. Auth is migrated from JWT to session-based using Flask-Login.

## Architecture

The app becomes a server-driven SPA using the Inertia.js protocol:

- Flask handles all routing — both the REST API (threads, messages, users) and Inertia page routes
- Inertia page routes return JSON with a component name and props; no separate client-side data-fetching layer is needed for page loads
- React renders page components on the client; Inertia intercepts link clicks and form submissions to make XHR requests instead of full page reloads
- WebSocket (Flask-SocketIO) remains unchanged for real-time message delivery; the client connects from within React page components
- Session-based auth replaces JWT: Flask-Login manages the session cookie, OAuth callback calls `login_user()`, and Inertia's redirect behavior works naturally with Flask's `redirect()`

**Page load data flow:**
```
Browser → Flask route → flask-inertia → JSON { component: "threads/ThreadList", props: {...} }
                                       → React renders ThreadListPage with those props
```

**Real-time data flow:**
```
React (useEffect in .page.tsx) → Socket.IO connect → server emits events → React state update
```

## Directory Structure

```
flask-example/
  app/
    templates/
      spa_root.html           ← single HTML shell with Inertia mount point
    auth/
      auth_routes.py          ← updated: Inertia page routes replacing REST auth endpoints
      auth_service.py         ← updated: removes JWT, session-based only
      oauth.py                ← unchanged
      decorators.py           ← updated: @login_required from Flask-Login
      jwt.py                  ← deleted
    messages/
    threads/
      thread_routes.py        ← gains Inertia page routes alongside existing REST routes
    users/
    spa/
      __init__.py
      spa_routes.py           ← catch-all route for client-side navigation
    static/
      dist/                   ← vite build output (gitignored)
    __init__.py
    config.py
    extensions.py             ← adds LoginManager, Inertia
    dependencies.py
  frontend/
    src/
      pages/
        auth/
          Login.page.tsx
          Login.layout.tsx
        threads/
          ThreadList.page.tsx
          ThreadList.layout.tsx
          ThreadDetail.page.tsx
          ThreadDetail.layout.tsx
        home/
          Home.page.tsx
          Home.layout.tsx
      components/             ← shadcn components output here
        Button.tsx
        Avatar.tsx
        Dialog.tsx
      hooks/
        useLocalStorage.ts
        useSocket.ts
      app.tsx                 ← Inertia setup, React root, resolves page components
      main.tsx                ← entry point
    index.html                ← Vite entry HTML
    vite.config.ts
    package.json
    pnpm-lock.yaml
    tsconfig.json
  tests/                      ← unchanged structure
  docs/
  Makefile
  Dockerfile
  docker-compose.yml
  lefthook.yml
```

## Page / Layout Convention

Every frontend page is split into two files:

- **`*.page.tsx`** — Inertia page component. Receives typed props from `usePage()`, manages side effects (WebSocket connections, etc.), and passes data down to the layout. This is the only file that imports from `@inertiajs/react`.
- **`*.layout.tsx`** — Pure presentation component. Receives props from the page, renders UI using Tailwind and shadcn components. No Inertia or socket awareness.

Example:

```tsx
// ThreadDetail.page.tsx
import { usePage } from '@inertiajs/react';
import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';
import { ThreadDetailLayout } from './ThreadDetail.layout';

interface Props {
  thread: Thread;
  messages: Message[];
}

export default function ThreadDetailPage() {
  const { thread, messages: initial } = usePage<Props>().props;
  const [messages, setMessages] = useState(initial);

  useEffect(() => {
    const socket = io();
    socket.emit('join', { thread_id: thread.id });
    socket.on('message', (msg) => setMessages((prev) => [...prev, msg]));
    return () => { socket.disconnect(); };
  }, [thread.id]);

  return <ThreadDetailLayout thread={thread} messages={messages} />;
}
```

```tsx
// ThreadDetail.layout.tsx
interface Props {
  thread: Thread;
  messages: Message[];
}

export function ThreadDetailLayout({ thread, messages }: Props) {
  // Tailwind + shadcn JSX only
}
```

## Auth: JWT to Session-Based

### Removed
- `app/auth/jwt.py` — deleted entirely
- JWT token generation and `@jwt_required` decorators across all route files

### Added
- `Flask-Login` to dependencies
- `LoginManager` initialized in `extensions.py`, registered in `create_app()`
- `UserMixin` added to `User` model (provides `is_authenticated`, `get_id()`, etc.)
- `user_loader` callback in `extensions.py` loads user by ID from the session

### Auth route changes

| Old | New |
|-----|-----|
| `POST /auth/login` → returns JWT JSON | `GET /auth/login` → Inertia renders `Login.page.tsx` |
| `GET /auth/oauth/google` → redirect | unchanged |
| `GET /auth/oauth/google/callback` → returns JWT | → `login_user(user)` + `redirect("/")` |
| `POST /auth/logout` → 200 JSON | `GET /auth/logout` → `logout_user()` + `redirect("/auth/login")` |

### Protection
All existing REST routes (`/api/threads`, `/api/messages`, `/api/users`) swap `@jwt_required` for `@login_required`. The session cookie is sent automatically, so WebSocket handshakes also have access to `current_user` without any token passing.

### Test fixtures
`tests/conftest.py` auth fixtures switch from generating JWT tokens to calling `login_user()` within the test request context.

## Flask-Inertia Integration

### Setup
```python
# extensions.py
from flask_inertia import Inertia
inertia = Inertia()

# __init__.py (create_app)
inertia.init_app(app)
app.config['INERTIA_TEMPLATE'] = 'spa_root.html'

# Flask-Login: redirect unauthenticated users to the login page route
login_manager.login_view = 'auth.login_page'
```

### Root template (`app/templates/spa_root.html`)
```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    {{ inertia_head() }}
  </head>
  <body>
    {{ inertia() }}
  </body>
</html>
```

### Catch-all route (`app/spa/spa_routes.py`)
```python
from flask import Blueprint
from flask_inertia import render_inertia
from flask_login import login_required

spa_bp = Blueprint('spa', __name__)

@spa_bp.route('/', defaults={'path': ''})
@spa_bp.route('/<path:path>')
@login_required
def index(path: str):
    return render_inertia('home/Home')
```

The `spa` blueprint must be registered **last** in `create_app()`, after all API blueprints, so that `/api/...` routes are matched first and the catch-all only handles unmatched paths.

### Page routes in domain blueprints
Inertia page routes live alongside their domain's REST routes:

```python
# app/threads/thread_routes.py

# REST route (unchanged)
@threads_bp.route('/api/threads', methods=['GET'])
@login_required
def list_threads_api(): ...

# Inertia page route (new)
@threads_bp.route('/threads')
@login_required
def threads_page():
    threads = make_thread_service().get_user_threads(current_user.id)
    return render_inertia('threads/ThreadList', props={
        'threads': [t.to_dict() for t in threads]
    })
```

### Vite manifest
`config.py` sets `INERTIA_ASSET_VERSION` from `app/static/dist/.vite/manifest.json` in production so Inertia knows when to force a full reload after a deploy.

## Frontend Stack

| Concern | Tool |
|---------|------|
| Build | Vite |
| Framework | React 18 + TypeScript |
| Routing | Inertia.js (`@inertiajs/react`) |
| Styling | Tailwind CSS |
| Components | shadcn/ui (output to `src/components/`) |
| Package manager | pnpm |
| Real-time | socket.io-client |

### shadcn configuration
shadcn is configured to output components to `src/components/` instead of the default `src/components/ui/`:

```json
// components.json
{
  "aliases": {
    "components": "@/components",
    "ui": "@/components"
  }
}
```

### `vite.config.ts`
```ts
import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

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
      '/socket.io': {
        target: 'http://localhost:5000',
        ws: true,
      },
    },
  },
});
```

### `app.tsx`
```tsx
import { createInertiaApp } from '@inertiajs/react';
import { createRoot } from 'react-dom/client';

createInertiaApp({
  resolve: (name) => {
    const pages = import.meta.glob('./pages/**/*.page.tsx', { eager: true });
    return pages[`./pages/${name}.page.tsx`];
  },
  setup({ el, App, props }) {
    createRoot(el).render(<App {...props} />);
  },
});
```

## Dev Workflow

### Running locally
```bash
make dev    # starts Postgres, Flask, and Vite concurrently
```

### Makefile targets
```makefile
db-up:
	docker compose up -d db

frontend-install:
	cd frontend && pnpm install

frontend-dev:
	cd frontend && pnpm dev

frontend-build:
	cd frontend && pnpm build

dev: db-up
	make -j2 run frontend-dev
```

### Lefthook additions
```yaml
pre-commit:
  commands:
    frontend-lint:
      glob: "frontend/src/**/*.{ts,tsx}"
      run: cd frontend && pnpm lint
    frontend-typecheck:
      glob: "frontend/src/**/*.{ts,tsx}"
      run: cd frontend && pnpm typecheck
```

## Testing

### Backend
- Existing unit/integration/e2e structure is unchanged
- Auth fixtures in `conftest.py` switch from JWT token generation to `login_user()` within the test request context
- The e2e test updates to follow the session-based OAuth callback flow

### Frontend
No frontend tests in scope for this iteration.

## Production Build

1. `cd frontend && pnpm build` — outputs assets to `app/static/dist/`
2. Flask starts — serves `spa_root.html` for all non-API paths; Vite manifest is read for asset versioning
3. Docker: `Dockerfile` gains a build stage that installs Node/pnpm and runs `pnpm build` before the Python stage copies `app/static/dist/`
