from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

class Message(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Chat(BaseModel):
    id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    title: str = "New Chat"
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
