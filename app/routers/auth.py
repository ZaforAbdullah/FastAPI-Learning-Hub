from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.exceptions import UnauthorizedError
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserResponse
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=Token)
async def login_oauth2_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth2 password flow — accepts form data (application/x-www-form-urlencoded).
    This is the endpoint the Swagger UI "Authorize" button calls.

        curl -X POST http://localhost:8000/auth/token\
          -d "username=admin&password=admin123"
    """
    service = UserService(db)
    user = await service.authenticate(form_data.username, form_data.password)
    if not user:
        raise UnauthorizedError("Incorrect username or password")

    token = AuthService.create_access_token({"sub": user.username, "is_admin": user.is_admin})
    return Token(access_token=token)


@router.post("/login", response_model=Token)
async def login_json(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    JSON login — friendlier for SPA and mobile clients.

        curl -X POST http://localhost:8000/auth/login\
          -H "Content-Type: application/json"\
          -d '{"username": "admin", "password": "admin123"}'
    """
    service = UserService(db)
    user = await service.authenticate(credentials.username, credentials.password)
    if not user:
        raise UnauthorizedError("Incorrect username or password")

    token = AuthService.create_access_token({"sub": user.username, "is_admin": user.is_admin})
    return Token(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the authenticated user's profile.

        curl http://localhost:8000/auth/me\
          -H "Authorization: Bearer <token>"
    """
    return current_user
