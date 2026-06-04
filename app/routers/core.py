"""
Demonstrates core FastAPI routing primitives in one place:
path params, query params, request body, headers, cookies, enums.
"""
from enum import Enum
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Cookie, Header, Path, Query, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/core", tags=["Core Concepts"])


# ── Path parameters ──────────────────────────────────────────────────────────

@router.get("/items/{item_id}")
async def get_item(item_id: int = Path(ge=1, description="Item ID")):
    """
    Path params are extracted from the URL and type-coerced automatically.
    Non-integers or values below 1 are rejected with 422.

        curl http://localhost:8000/core/items/42
    """
    return {"item_id": item_id, "name": f"Item #{item_id}"}


class ItemCategory(str, Enum):
    electronics = "electronics"
    clothing = "clothing"
    food = "food"


@router.get("/categories/{category}")
async def get_category(category: ItemCategory):
    """
    Enum path param — only the declared values are accepted.
    Swagger UI renders this as a dropdown.

        curl http://localhost:8000/core/categories/electronics
    """
    return {"category": category, "description": f"Showing {category.value} items"}


# ── Query parameters ─────────────────────────────────────────────────────────

@router.get("/search")
async def search_items(
    q: str = Query(min_length=2, description="Search term"),
    limit: int = Query(default=10, ge=1, le=100),
    category: Optional[str] = Query(default=None),
    tags: list[str] = Query(default=[]),   # ?tags=a&tags=b → ["a", "b"]
):
    """
    Query params without defaults are required; those with defaults are optional.
    Repeat a param name to get a list: ?tags=sale&tags=new

        curl "http://localhost:8000/core/search?q=shirt&limit=5&tags=sale&tags=new"
    """
    return {
        "query": q,
        "limit": limit,
        "category": category,
        "tags": tags,
        "results": [f"Result for '{q}' #{i}" for i in range(limit)],
    }


# ── Request body ─────────────────────────────────────────────────────────────

class CreateItemRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Must be positive")
    quantity: int = Field(ge=0, default=0)
    tags: list[str] = []


class ItemResponse(BaseModel):
    id: int
    name: str
    price: float
    quantity: int
    tags: list[str]


@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(item: CreateItemRequest):
    """
    A Pydantic model as a parameter means FastAPI reads the JSON body.
    response_model filters the output; status_code sets the success status.

        curl -X POST http://localhost:8000/core/items\
          -H "Content-Type: application/json"\
          -d '{"name": "Laptop", "price": 999.99, "quantity": 5}'
    """
    return ItemResponse(id=1, **item.model_dump())


# ── Mixed params ─────────────────────────────────────────────────────────────

class UpdateItemRequest(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)


@router.put("/items/{item_id}")
async def update_item(
    item_id: int = Path(ge=1),
    notify: bool = Query(default=False),
    item: UpdateItemRequest = Body(...),
):
    """
    Path + query + body in a single endpoint. FastAPI resolves the source of each
    param from its type: path template → path, primitive → query, model → body.

        curl -X PUT "http://localhost:8000/core/items/42?notify=true"\
          -H "Content-Type: application/json"\
          -d '{"price": 899.99}'
    """
    return {"item_id": item_id, "notify": notify, "updated": item.model_dump(exclude_none=True)}


# ── Headers ──────────────────────────────────────────────────────────────────

@router.get("/headers")
async def read_headers(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    user_agent: Optional[str] = Header(default=None),
):
    """
    Header() reads from request headers. FastAPI converts hyphens to underscores
    for the param name; use alias= to keep the exact header name.

        curl http://localhost:8000/core/headers -H "X-API-Key: mysecret"
    """
    return {"api_key_present": x_api_key is not None, "user_agent": user_agent}


# ── Cookies ──────────────────────────────────────────────────────────────────

@router.get("/cookies")
async def read_cookies(session_id: Optional[str] = Cookie(default=None)):
    """
        curl http://localhost:8000/core/cookies --cookie "session_id=abc123"
    """
    return {"session_id": session_id, "authenticated": session_id is not None}


# ── Annotated style ──────────────────────────────────────────────────────────

@router.get("/annotated/{user_id}")
async def annotated_style(
    user_id: Annotated[int, Path(ge=1)],
    active: Annotated[bool, Query()] = True,
):
    """
    Annotated[type, constraint] is the modern Python 3.9+ equivalent of
    `user_id: int = Path(ge=1)`. Both work identically.

        curl "http://localhost:8000/core/annotated/5?active=false"
    """
    return {"user_id": user_id, "active": active}
