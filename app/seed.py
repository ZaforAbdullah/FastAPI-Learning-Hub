"""
Database seeder — skips rows that already exist, safe to call repeatedly.
Called from lifespan on startup (debug mode) and from the root seed.py script.
"""
import logging
import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

SEED_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "full_name": "Admin User",
        "password": "admin123",
        "is_admin": True,
    },
    {
        "email": "alice@example.com",
        "username": "alice",
        "full_name": "Alice Smith",
        "password": "alice123",
        "is_admin": False,
    },
]


async def run_seed() -> None:
    async with AsyncSessionLocal() as db:
        created = await _seed_users(db)
        await db.commit()

    if created:
        logger.info(f"Seeded {len(created)} user(s): {', '.join(created)}")
    else:
        logger.info("Seed: all users already exist, nothing inserted")


async def _seed_users(db: AsyncSession) -> list[str]:
    created = []
    for data in SEED_USERS:
        result = await db.execute(select(User).where(User.username == data["username"]))
        if result.scalar_one_or_none():
            continue
        db.add(User(
            email=data["email"],
            username=data["username"],
            full_name=data["full_name"],
            hashed_password=AuthService.hash_password(data["password"]),
            is_admin=data["is_admin"],
        ))
        created.append(data["username"])
    return created

if __name__ == "__main__":
    asyncio.run(run_seed())
