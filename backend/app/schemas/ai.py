from pydantic import BaseModel, Field


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class AIChatResponse(BaseModel):
    answer: str
    context_domains: list[str]


class AIQuickActionRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=1000)
