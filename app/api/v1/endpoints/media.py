# app/api/v1/endpoints/media.py
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.dependencies import get_current_shop, get_current_user
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

