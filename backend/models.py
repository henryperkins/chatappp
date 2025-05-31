# Pydantic models for request/response validation
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal
from datetime import datetime


class ChatMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)
    command: Optional[Literal["/explain", "/refactor", "/tests", "/summarize"]] = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    timestamp: datetime
    model: Optional[str] = None

    class Config:
        orm_mode = True


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]
    total: int


class SettingsUpdate(BaseModel):
    model: Optional[str] = None
    provider: Optional[str] = Field(None)
    max_tokens: Optional[int] = Field(None, ge=1, le=4096)
    temperature: Optional[float] = Field(None, ge=0, le=2)

    @validator("model")
    def validate_model(cls, v):
        allowed_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
        if v and v not in allowed_models:
            raise ValueError(f"Model must be one of {allowed_models}")
        return v

    @validator("provider")
    def validate_provider(cls, v):
        allowed = ["openai", "azure"]
        if v and v not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v


class StreamChunk(BaseModel):
    type: Literal["content", "error", "done"]
    data: Optional[str] = None
    error: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
