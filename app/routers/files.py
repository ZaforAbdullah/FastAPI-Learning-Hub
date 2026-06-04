"""
File upload, download, and form handling.

Note: UploadFile + Form fields share the same multipart request.
You cannot mix a Pydantic JSON body with Form fields in the same endpoint.
"""
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/files", tags=["Files & Forms"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(default=None),
):
    """
        curl -X POST http://localhost:8000/files/upload\
          -F "file=@/path/to/image.jpg"\
          -F "description=My photo"
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(422, detail=f"File type '{file.content_type}' not allowed")

    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(413, detail="File too large (max 5 MB)")

    ext = Path(file.filename or "file").suffix
    unique_name = f"{uuid.uuid4()}{ext}"
    (UPLOAD_DIR / unique_name).write_bytes(content)

    return {
        "filename": unique_name,
        "original_name": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "description": description,
        "url": f"/files/download/{unique_name}",
    }


@router.post("/upload-multiple")
async def upload_multiple_files(files: list[UploadFile] = File(...)):
    """
        curl -X POST http://localhost:8000/files/upload-multiple\
          -F "files=@photo1.jpg"\
          -F "files=@photo2.png"
    """
    results = []
    for file in files:
        content = await file.read()
        ext = Path(file.filename or "file").suffix
        unique_name = f"{uuid.uuid4()}{ext}"
        (UPLOAD_DIR / unique_name).write_bytes(content)
        results.append({"original": file.filename, "saved_as": unique_name, "size": len(content)})

    return {"uploaded": len(results), "files": results}


@router.get("/download/{filename}")
async def download_file(filename: str):
    """
        curl -OJ http://localhost:8000/files/download/<filename>
    """
    # Path(filename).name strips any directory components to prevent traversal
    safe_path = UPLOAD_DIR / Path(filename).name
    if not safe_path.exists():
        raise HTTPException(404, detail="File not found")

    return FileResponse(path=safe_path, filename=filename, media_type="application/octet-stream")


@router.post("/form-data")
async def handle_form(
    name: str = Form(...),
    email: str = Form(...),
    age: int = Form(...),
    newsletter: bool = Form(default=False),
):
    """
    Plain form submission (no file).

        curl -X POST http://localhost:8000/files/form-data\
          -F "name=Alice" -F "email=alice@example.com" -F "age=30"
    """
    return {"name": name, "email": email, "age": age, "newsletter": newsletter}
