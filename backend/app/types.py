from typing import List

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequestBody(BaseModel):
    messages: List[ChatMessage]
