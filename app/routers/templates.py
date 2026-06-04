from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/web", tags=["Templates"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
        curl http://localhost:8000/web/
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "FastAPI Learning",
        "features": [
            "Path & Query Parameters",
            "Request Body & Validation",
            "JWT Authentication",
            "WebSockets",
            "Background Tasks",
            "File Upload",
        ],
    })


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = "Guest"):
    """
        curl "http://localhost:8000/web/dashboard?username=Alice"
    """
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": f"Dashboard — {username}",
        "features": [],
    })
