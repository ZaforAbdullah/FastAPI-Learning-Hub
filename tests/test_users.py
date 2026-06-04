"""
Tests for user CRUD endpoints.
Demonstrates: status codes, JSON body, auth headers, error cases.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/users", json={
        "email": "alice@example.com",
        "username": "alice",
        "password": "secure123",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "hashed_password" not in data  # never expose password


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@example.com", "username": "user1", "password": "pass1234"}
    await client.post("/users", json=payload)
    # Second attempt with same email
    response = await client.post("/users", json={**payload, "username": "user2"})
    assert response.status_code == 409
    assert "email" in response.json()["error"].lower()


@pytest.mark.asyncio
async def test_create_user_invalid_password(client: AsyncClient):
    """Password must contain a digit — custom validator."""
    response = await client.post("/users", json={
        "email": "bob@example.com",
        "username": "bob",
        "password": "nodigitshere",  # fails @field_validator
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_own_profile(client: AsyncClient, auth_headers: dict):
    response = await client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_profile_unauthenticated(client: AsyncClient):
    response = await client.get("/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_own_profile(
    client: AsyncClient,
    registered_user: dict,
    auth_headers: dict,
):
    user_id = registered_user["id"]
    response = await client.patch(
        f"/users/{user_id}",
        json={"full_name": "Test User Updated"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Test User Updated"


@pytest.mark.asyncio
async def test_get_nonexistent_user(client: AsyncClient, auth_headers: dict):
    response = await client.get("/users/99999", headers=auth_headers)
    assert response.status_code == 404
