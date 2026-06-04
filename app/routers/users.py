from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_admin, get_current_user
from app.dependencies.database import get_db
from app.dependencies.pagination import PaginationParams
from app.exceptions import ForbiddenError
from app.models.user import User
from app.schemas.user import UserCreate, UserListResponse, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Public registration endpoint.

        curl -X POST http://localhost:8000/users\
          -H "Content-Type: application/json"\
          -d '{"email":"bob@example.com","username":"bob","password":"Secret1!"}'
    """
    return await UserService(db).create_user(data)


@router.get("", response_model=UserListResponse)
async def list_users(
    pagination: PaginationParams = Depends(PaginationParams),
    is_active: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None, description="Search username or email"),
    _: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Paginated user list. Admin only.

        curl "http://localhost:8000/users?page=1&size=10&search=alice"\
          -H "Authorization: Bearer <admin_token>"
    """
    return await UserService(db).list_users(pagination, is_active=is_active, search=search)


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Must be defined before /{user_id} to prevent "me" being parsed as an integer.

        curl http://localhost:8000/users/me -H "Authorization: Bearer <token>"
    """
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
        curl http://localhost:8000/users/1 -H "Authorization: Bearer <token>"
    """
    return await UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Users can update their own profile; admins can update anyone.

        curl -X PATCH http://localhost:8000/users/1\
          -H "Authorization: Bearer <token>"\
          -H "Content-Type: application/json"\
          -d '{"full_name": "Alice Smith"}'
    """
    if current_user.id != user_id and not current_user.is_admin:
        raise ForbiddenError("You can only update your own profile")

    return await UserService(db).update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """
    Admin only. Returns 204 No Content on success.

        curl -X DELETE http://localhost:8000/users/1\
          -H "Authorization: Bearer <admin_token>"
    """
    await UserService(db).delete_user(user_id)
