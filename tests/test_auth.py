"""
Tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user: dict):
    response = await client.post("/auth/login", json={
        "username": "testuser",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, registered_user: dict):
    response = await client.post("/auth/login", json={
        "username": "testuser",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_user(client: AsyncClient):
    response = await client.post("/auth/login", json={
        "username": "ghost",
        "password": "doesntmatter",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_oauth2_form_login(client: AsyncClient, registered_user: dict):
    """OAuth2 form endpoint — used by Swagger UI Authorize button."""
    response = await client.post(
        "/auth/token",
        data={"username": "testuser", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_get_me_with_valid_token(client: AsyncClient, auth_headers: dict):
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_with_invalid_token(client: AsyncClient):
    response = await client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_core_query_params(client: AsyncClient):
    """Test core concepts router — search endpoint."""
    response = await client.get("/core/search?q=laptop&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "laptop"
    assert len(data["results"]) == 5


@pytest.mark.asyncio
async def test_core_path_param_validation(client: AsyncClient):
    """item_id must be >= 1."""
    response = await client.get("/core/items/0")
    assert response.status_code == 422

    response = await client.get("/core/items/abc")
    assert response.status_code == 422

    response = await client.get("/core/items/5")
    assert response.status_code == 200
