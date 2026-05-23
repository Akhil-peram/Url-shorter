import secrets
import string
from contextlib import asynccontextmanager

import aiosqlite
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

DB_PATH = "urls.db"
ALPHABET = string.ascii_letters + string.digits


async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db():
    db = await get_db()
    await db.execute(
        """CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            target TEXT NOT NULL,
            visits INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_slug ON urls(slug)"
    )
    await db.commit()
    await db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ShortenRequest(BaseModel):
    url: HttpUrl


def generate_slug(length=6):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, slug: str = None):
    return templates.TemplateResponse(
        request, "index.html",
        {"slug": slug, "base_url": str(request.base_url)},
    )


@app.post("/shorten")
async def shorten(req: ShortenRequest, request: Request):
    db = await get_db()
    cursor = await db.execute("SELECT slug FROM urls WHERE target = ?", (str(req.url),))
    existing = await cursor.fetchone()
    if existing:
        await db.close()
        return {"slug": existing["slug"], "short_url": f"{request.base_url}{existing['slug']}"}

    slug = generate_slug()
    for _ in range(10):
        cursor = await db.execute("SELECT 1 FROM urls WHERE slug = ?", (slug,))
        if not await cursor.fetchone():
            break
        slug = generate_slug()
    else:
        await db.close()
        raise HTTPException(status_code=500, detail="Could not generate unique slug")

    await db.execute("INSERT INTO urls (slug, target) VALUES (?, ?)", (slug, str(req.url)))
    await db.commit()
    await db.close()
    return {"slug": slug, "short_url": f"{request.base_url}{slug}"}


@app.get("/{slug}")
async def redirect(slug: str, request: Request):
    db = await get_db()
    cursor = await db.execute("SELECT target FROM urls WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if row is None:
        await db.close()
        return templates.TemplateResponse(
            request, "index.html",
            {"slug": None, "base_url": str(request.base_url), "error": "Link not found"},
            status_code=404,
        )
    await db.execute("UPDATE urls SET visits = visits + 1 WHERE slug = ?", (slug,))
    await db.commit()
    await db.close()
    return RedirectResponse(url=row["target"], status_code=302)


def run():
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
