from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.journal import Mood


class JournalTagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip().lower()
        if not value:
            raise ValueError("tag name cannot be empty")
        return value


class JournalTagRead(JournalTagCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class JournalUpsert(BaseModel):
    mood: Mood
    content: str = Field(max_length=20000)
    tag_ids: list[int] = Field(default_factory=list)


class JournalRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entry_date: date
    mood: Mood
    content: str
    tags: list[JournalTagRead]
    created_at: datetime
    updated_at: datetime
