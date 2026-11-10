# app/integrations/storage.py
import aioboto3
from app.core.config import settings
from app.core.exceptions import BadRequestException

ALLOWED_EXTENSIONS = {"image/png", "image/jpeg", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5 MB

class StorageService:
    def __init__(self):
        self.session = aioboto3.Session()

    async def generate_presigned_upload_url(
        self, file_path: str, content_type: str, expires_in: int = 900
    ) -> dict:
        if content_type not in ALLOWED_EXTENSIONS:
            raise BadRequestException(f"Format de fichier '{content_type}' non supporté. PNG, JPEG, WebP uniquement.")

        async with self.session.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        ) as s3_client:
            url = await s3_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": settings.S3_BUCKET_NAME,
                    "Key": file_path,
                    "ContentType": content_type,
                },
                ExpiresIn=expires_in,
            )
            public_url = f"{settings.S3_PUBLIC_DOMAIN}/{file_path}"
            return {"upload_url": url, "public_url": public_url, "file_path": file_path}

storage_service = StorageService()

