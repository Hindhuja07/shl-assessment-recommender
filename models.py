from typing import List, Literal
from pydantic import BaseModel, Field, HttpUrl, field_validator


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: List[Message] = Field(min_length=1)


class Recommendation(BaseModel):
    name: str
    url: str
    test_type: str = ""

    @field_validator("name", "url")
    @classmethod
    def not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("blank value")
        return value.strip()


class ChatResponse(BaseModel):
    reply: str
    recommendations: List[Recommendation]
    end_of_conversation: bool = False
