import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import create_tables
from app.exceptions import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware
from app.routers import advanced, auth, core, files, templates, users, websockets
from app.seed import run_seed

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    await create_tables()
    if settings.debug:
        await run_seed()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## FastAPI Learning Project

Covers path/query params, request body, JWT auth, async SQLAlchemy,
background tasks, WebSockets, file upload, caching, rate limiting, and more.

Use `/auth/token` (form) or `/auth/login` (JSON) to get a Bearer token,
then click **Authorize** in Swagger UI.
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "Core Concepts", "description": "Path/query params, body, headers, cookies"},
        {"name": "Authentication", "description": "JWT login and token management"},
        {"name": "Users", "description": "User CRUD with pagination and filtering"},
        {"name": "Files & Forms", "description": "File upload, download, form handling"},
        {"name": "Advanced Features", "description": "Background tasks, caching, rate limiting"},
        {"name": "WebSockets", "description": "Real-time bidirectional communication"},
        {"name": "Templates", "description": "Server-rendered HTML pages"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(core.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(websockets.router)
app.include_router(advanced.router)
app.include_router(templates.router)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "healthy"}
