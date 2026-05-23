# shrtnr — URL Shortener
A minimal, cross-platform URL shortener built with FastAPI.
## Quick Start
```bash
uv sync
uv run uvicorn main:app --reload
```
Open http://localhost:8000
## Functions
### `get_db()`
Opens a connection to the SQLite database (`urls.db`) with row factory enabled.
### `init_db()`
Creates the `urls` table and an index on `slug` if they don't exist. Runs at startup.
### `lifespan(app)`
Async context manager that initializes the database on startup and cleans up on shutdown.
### `generate_slug(length=6)`
Generates a random 6-character alphanumeric slug using `secrets.choice`.
### `index(request, slug=None)`
`GET /` — Renders the home page. Accepts an optional `?slug=` query parameter to pre-populate a result.
### `shorten(req, request)`
`POST /shorten` — Accepts `{"url": "..."}`, checks for duplicates, generates a unique slug, stores in DB, returns `{"slug": ..., "short_url": ...}`.
### `redirect(slug, request)`
`GET /{slug}` — Looks up the slug, increments visit counter, and issues a 302 redirect. Returns a 404 page if not found.
### `run()`
Entry point that starts the uvicorn server on `0.0.0.0:8000` with hot-reload.
## Tools & Dependencies
| Tool/Package | Purpose |
|---|---|
| **FastAPI** | Web framework for building the API and serving templates |
| **Uvicorn** | ASGI server with hot-reload support |
| **Jinja2** | Templating engine for server-side HTML rendering |
| **aiosqlite** | Async SQLite driver for database operations |
| **Pydantic** | Request validation (`HttpUrl` ensures valid URLs) |
| **secrets** | Cryptographically secure random slug generation |
| **uv** | Python project and package manager (replaces pip/poetry) |
| **SQLite** | Zero-config, file-based database (cross-platform) |
## Database Schema
```sql
urls (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    slug        TEXT UNIQUE NOT NULL,
    target      TEXT NOT NULL,
    visits      INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```
