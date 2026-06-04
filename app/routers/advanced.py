"""
Background tasks, in-memory caching, rate limiting, streaming, async concurrency.
"""
import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/advanced", tags=["Advanced Features"])


# ── Background tasks ─────────────────────────────────────────────────────────

def send_welcome_email(email: str, username: str) -> None:
    logger.info(f"[bg] sending welcome email to {email}")
    time.sleep(2)  # simulate slow third-party email call
    logger.info(f"[bg] email sent to {email} for {username}")


def log_action(user_id: int, action: str) -> None:
    logger.info(f"[audit] user_id={user_id} action={action}")


@router.post("/register-with-email")
async def register_with_background_email(
    email: str,
    username: str,
    background_tasks: BackgroundTasks,
):
    """
    Response is returned immediately; the email task runs after.
    For heavy workloads use Celery or ARQ — background tasks share the worker process.

        curl -X POST "http://localhost:8000/advanced/register-with-email?email=a@b.com&username=alice"
    """
    background_tasks.add_task(send_welcome_email, email, username)
    background_tasks.add_task(log_action, 0, "register")
    return {"message": "Registered — welcome email on its way.", "username": username}


# ── In-memory cache ──────────────────────────────────────────────────────────

_cache: dict[str, tuple[Any, float]] = {}


def cache_get(key: str) -> Any | None:
    if key in _cache:
        value, expires_at = _cache[key]
        if time.time() < expires_at:
            return value
        del _cache[key]
    return None


def cache_set(key: str, value: Any, ttl: int = 60) -> None:
    _cache[key] = (value, time.time() + ttl)


@router.get("/expensive-data")
async def get_expensive_data(force_refresh: bool = False):
    """
    Cached for 60 seconds. First call takes ~1s; subsequent calls are instant.

        curl http://localhost:8000/advanced/expensive-data
        curl "http://localhost:8000/advanced/expensive-data?force_refresh=true"
    """
    key = "expensive_data"
    if not force_refresh:
        cached = cache_get(key)
        if cached:
            return {**cached, "from_cache": True}

    await asyncio.sleep(1)  # simulate slow DB / external API
    data = {
        "result": [{"id": i, "value": i * 42} for i in range(10)],
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "from_cache": False,
    }
    cache_set(key, data, ttl=60)
    return data


# ── Rate limiting ─────────────────────────────────────────────────────────────

# Sliding-window store per IP. Use Redis for multi-process deployments.
_rate_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(ip: str, max_req: int = 5, window: int = 60) -> bool:
    now = time.time()
    _rate_store[ip] = [t for t in _rate_store[ip] if t > now - window]
    if len(_rate_store[ip]) >= max_req:
        return False
    _rate_store[ip].append(now)
    return True


@router.get("/rate-limited")
async def rate_limited_endpoint(request: Request):
    """
    5 requests per minute per IP. Hit it 6 times to see the 429 response.

        for i in {1..6}; do curl http://localhost:8000/advanced/rate-limited; echo; done
    """
    ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 5 requests/minute.",
            headers={"Retry-After": "60"},
        )
    return {"message": "ok", "client_ip": ip}


# ── Streaming response ────────────────────────────────────────────────────────

async def _generate(n: int):
    for i in range(n):
        yield f"data: chunk {i} at {datetime.now(timezone.utc).isoformat()}\n\n"
        await asyncio.sleep(0.5)


@router.get("/stream")
async def stream_data(chunks: int = 5):
    """
    Server-Sent Events stream. The client receives chunks as they're produced.

        curl -N "http://localhost:8000/advanced/stream?chunks=5"
    """
    return StreamingResponse(_generate(chunks), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})


# ── Async concurrency ─────────────────────────────────────────────────────────

async def _fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.3)
    return {"user_id": user_id, "name": f"User {user_id}"}


async def _fetch_orders(user_id: int) -> dict:
    await asyncio.sleep(0.3)
    return {"user_id": user_id, "orders": [f"Order {i}" for i in range(3)]}


@router.get("/concurrent/{user_id}")
async def concurrent_requests(user_id: int):
    """
    asyncio.gather runs both coroutines at the same time.
    Two 0.3s calls finish in ~0.3s total, not 0.6s.

        curl http://localhost:8000/advanced/concurrent/42
    """
    start = time.perf_counter()
    user, orders = await asyncio.gather(_fetch_user(user_id), _fetch_orders(user_id))
    return {
        "user": user,
        "orders": orders,
        "elapsed_ms": round((time.perf_counter() - start) * 1000, 1),
    }
