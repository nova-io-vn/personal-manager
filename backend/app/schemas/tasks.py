from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=10000)
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    note: str | None = Field(default=None, max_length=10000)
    due_date: date | None = None
    completed: bool | None = None


class TaskRead(TaskCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    completed: bool
    created_at: datetime
    updated_at: datetime
