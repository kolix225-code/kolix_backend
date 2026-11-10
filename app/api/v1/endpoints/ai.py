# app/api/v1/endpoints/ai.py
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_shop, get_current_user
from app.models.shop import Shop
from app.models.user import User
from app.schemas.ai import AiChatRequest, AiChatResponse
from app.schemas.common import StandardResponse
from app.services.ai_service import AiService

router = APIRouter(prefix="/ai", tags=["Assistant Kolix AI"])

@router.post("/chat", response_model=StandardResponse[AiChatResponse])
async def chat_with_ai(
    data: AiChatRequest,
    shop: Annotated[Shop, Depends(get_current_shop)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Dialogue avec l'assistant exécutif Kolix AI pour booster ses ventes COD."""
    shop_context = {
        "shop_name": shop.name,
        "plan": shop.plan,
        "orders_count": shop.orders_count
    }
    msgs = [{"role": m.role, "content": m.content} for m in data.messages]
    reply = await AiService.generate_response(msgs, shop_context)
    return StandardResponse(data=AiChatResponse(role="assistant", content=reply))

