# FastAPI Learning Hub

A single codebase that covers every major FastAPI concept — organized in production-style layers so you can trace how a real request flows through the stack.

---

## Architecture

```
Request → Middleware → Router → Dependency → Service → Repository → Database
                                                  ↓
                                          Exception Handler
```

| Layer | Responsibility |
|-------|---------------|
| Routers | HTTP surface — parse input, call service, return response |
| Services | Business logic and cross-cutting rules |
| Repositories | All database queries in one place |
| Dependencies | Reusable injectables (DB session, auth, pagination) |
| Schemas | Pydantic — request validation and response shaping |
| Models | SQLAlchemy — table definitions |

---

## Folder structure

```
app/
├── main.py               # App factory, middleware, CORS, routers, lifespan
├── config.py             # Settings via pydantic-settings (.env)
├── database.py           # Async SQLAlchemy engine + session factory
├── seed.py               # Dev seed (admin + alice)
├── models/user.py        # SQLAlchemy ORM model
├── schemas/user.py       # Pydantic request/response schemas
├── routers/
│   ├── core.py           # Path params, query params, body, headers, cookies
│   ├── auth.py           # JWT — form + JSON login, /me
│   ├── users.py          # Full CRUD with pagination and filtering
│   ├── files.py          # Single/multi upload, download, form-only
│   ├── advanced.py       # Background tasks, caching, rate limiting, streaming
│   ├── websockets.py     # Echo, broadcast chat, server push
│   └── templates.py      # Jinja2 HTML pages
├── services/
│   ├── user_service.py
│   └── auth_service.py   # bcrypt hashing, JWT encoding
├── repositories/
│   └── user_repository.py
├── dependencies/
│   ├── auth.py           # get_current_user, get_current_admin
│   ├── database.py       # get_db (yield dependency)
│   └── pagination.py     # PaginationParams
├── middleware/logging.py # Request ID + timing headers
├── exceptions/handlers.py
├── static/               # Served at /static/
└── templates/            # Jinja2 .html files
alembic/                  # Migration scripts
tests/
├── conftest.py           # Fixtures and dependency overrides
├── test_users.py
└── test_auth.py
```

---

## Setup

### Local (SQLite)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # defaults work out of the box
uvicorn app.main:app --reload
open http://localhost:8000/docs
```

Seed users are created automatically on first startup when `DEBUG=true`.

### Docker (PostgreSQL + Redis)

```bash
docker compose up --build
open http://localhost:8000/docs
```

### Tests

```bash
pytest -v
pytest tests/test_auth.py -v
pytest -k "login" -v
```

---

## Seed credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| User | `alice` | `alice123` |

Get a token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

---

## API reference

### Auth
| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/auth/token` | — | OAuth2 form login (Swagger UI uses this) |
| POST | `/auth/login` | — | JSON login |
| GET | `/auth/me` | ✓ | Current user |

### Users
| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/users` | — | Register |
| GET | `/users` | Admin | Paginated list + search |
| GET | `/users/me` | ✓ | Own profile |
| GET | `/users/{id}` | ✓ | Any user |
| PATCH | `/users/{id}` | ✓ | Own profile, or any if admin |
| DELETE | `/users/{id}` | Admin | — |

### Core concepts
| Method | Path | Demonstrates |
|--------|------|-------------|
| GET | `/core/items/{id}` | Path param + type coercion |
| GET | `/core/categories/{cat}` | Enum path param |
| GET | `/core/search` | Query params, multi-value list |
| POST | `/core/items` | Request body, response model, status code |
| PUT | `/core/items/{id}` | Mixed path + query + body |
| GET | `/core/headers` | Custom request headers |
| GET | `/core/cookies` | Cookie reading |
| GET | `/core/annotated/{id}` | `Annotated[type, constraint]` style |

### Files
| Method | Path | Demonstrates |
|--------|------|-------------|
| POST | `/files/upload` | UploadFile + Form field |
| POST | `/files/upload-multiple` | Multiple files |
| GET | `/files/download/{name}` | FileResponse |
| POST | `/files/form-data` | Form fields only (no file) |

### Advanced
| Method | Path | Demonstrates |
|--------|------|-------------|
| POST | `/advanced/register-with-email` | BackgroundTasks |
| GET | `/advanced/expensive-data` | In-memory cache with TTL |
| GET | `/advanced/rate-limited` | Sliding-window rate limiter (5/min) |
| GET | `/advanced/stream` | StreamingResponse / SSE |
| GET | `/advanced/concurrent/{id}` | `asyncio.gather` concurrency |

### WebSockets
| URL | Demonstrates |
|-----|-------------|
| `ws://localhost:8000/ws/echo` | Basic echo |
| `ws://localhost:8000/ws/chat/{room}/{username}` | Broadcast chat room |
| `ws://localhost:8000/ws/live-feed` | Server push (price ticks) |

---

## Key patterns

**Dependency injection** — `Depends(get_db)` injects a session; `Depends(get_current_user)` validates the JWT and fetches the user. Dependencies chain: `get_current_admin` calls `get_current_user` internally.

**Yield dependency** — `get_db` yields the session, commits on success, rolls back on exception, then closes. The route runs between `yield` and cleanup.

**Repository / Service split** — repositories own SQL; services own rules. Routes stay thin.

**Response model filtering** — `response_model=UserResponse` strips `hashed_password` from the output even if the ORM object carries it.

**Lifespan** — `@asynccontextmanager async def lifespan(app)` replaces `@app.on_event`. Code before `yield` runs on startup; code after runs on shutdown.

**Exception hierarchy** — raise `NotFoundError("User", id)` anywhere; the registered handler converts it to a 404 JSON response.

**Async SQLAlchemy** — all queries are `await`-ed so the event loop can serve other requests while waiting on the DB.

---

## Alembic

```bash
# After changing a model:
alembic revision --autogenerate -m "add phone column"
alembic upgrade head

# Roll back:
alembic downgrade -1
```
