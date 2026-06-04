from math import ceil
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.pagination import PaginationParams
from app.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserListResponse, UserUpdate
from app.services.auth_service import AuthService


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def create_user(self, data: UserCreate) -> User:
        if await self.repo.get_by_email(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered")
        if await self.repo.get_by_username(data.username):
            raise ConflictError(f"Username '{data.username}' is already taken")

        hashed = AuthService.hash_password(data.password)
        return await self.repo.create(data, hashed)

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def list_users(
        self,
        pagination: PaginationParams,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> UserListResponse:
        users, total = await self.repo.list(
            offset=pagination.offset,
            limit=pagination.size,
            is_active=is_active,
            search=search,
        )
        return UserListResponse(
            items=users,
            total=total,
            page=pagination.page,
            size=pagination.size,
            pages=ceil(total / pagination.size) if total else 0,
        )

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        return await self.repo.update(user, data)

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user(user_id)
        await self.repo.delete(user)

    async def authenticate(self, username: str, password: str) -> Optional[User]:
        user = await self.repo.get_by_username(username)
        if not user:
            return None
        if not AuthService.verify_password(password, user.hashed_password):
            return None
        return user
