# app/schemas/ai.py
from typing import List, Optional
from app.schemas.common import BaseSchema

class AiChatMessage(BaseSchema):
    role: str # user, assistant, system
    content: str

class AiChatRequest(BaseSchema):
    messages: List[AiChatMessage]
    stream: bool = False

class AiChatResponse(BaseSchema):
    role: str = "assistant"
    content: str

