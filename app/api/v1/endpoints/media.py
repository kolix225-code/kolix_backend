# app/api/v1/endpoints/media.py
import os
import uuid
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.core.dependencies import get_current_shop, get_current_user
from app.core.exceptions import NotFoundException
from app.integrations.storage import storage_service
from app.models.shop import Shop
from app.models.user import User
from app.schemas.common import StandardResponse

router = APIRouter(prefix="/media", tags=["Médias & Téléversement S3"])

class PresignRequest(BaseModel):
    filename: str
    content_type: str

@router.post("/presign-upload", response_model=StandardResponse[dict])
async def get_presigned_upload_url(
    data: PresignRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Générer une URL présignée S3 / MinIO pour téléversement direct sans surcharge backend."""
    extension = data.filename.split(".")[-1] if "." in data.filename else "webp"
    unique_key = f"shops/{shop.id}/uploads/{uuid.uuid4()}.{extension}"

    result = await storage_service.generate_presigned_upload_url(
        file_path=unique_key,
        content_type=data.content_type
    )
    return StandardResponse(
        message="URL de téléversement direct générée avec succès (validité 15 min).",
        data=result
    )

@router.post("/upload", response_model=StandardResponse[dict])
async def upload_media_file(
    file: UploadFile = File(...),
    current_user: Annotated[User, Depends(get_current_user)] = None
):
    """Téléversement direct d'une image produit vers MinIO / S3 avec persistance."""
    content = await file.read()
    extension = file.filename.split(".")[-1] if "." in file.filename else "webp"
    unique_key = f"products/{uuid.uuid4()}.{extension}"

    content_type = file.content_type or "image/webp"
    public_url = await storage_service.upload_bytes(content, unique_key, content_type)

    return StandardResponse(
        message="Image téléversée avec succès sur MinIO.",
        data={
            "url": public_url,
            "filename": file.filename,
            "content_type": content_type
        }
    )

@router.get("/files/{filename}")
async def get_local_media_file(filename: str):
    """Servir les fichiers médias locaux si le bucket MinIO est indisponible."""
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    safe_name = os.path.basename(filename)
    path = os.path.join(uploads_dir, safe_name)
    if not os.path.isfile(path):
        raise NotFoundException("Fichier", filename)
    return FileResponse(path)

