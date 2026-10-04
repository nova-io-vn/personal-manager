from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.calendar import RepeatType


class ScheduleCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(min_length=1, max_length=20)


class ScheduleCategoryRead(ScheduleCategoryCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class ScheduleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    start_datetime: datetime
    end_datetime: datetime
    category_id: int | None = None
    color: str | None = Field(default=None, max_length=20)
    reminder_minutes: int = Field(default=0, ge=0)
    repeat_type: RepeatType = RepeatType.NONE
    repeat_until: datetime | None = None
    completed: bool = False

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("title cannot be empty")
        return value.strip()

    @model_validator(mode="after")
    def validate_range_and_repeat(self):
        if self.end_datetime <= self.start_datetime:
            raise ValueError("end_datetime must be after start_datetime")
        if self.repeat_type == RepeatType.NONE and self.repeat_until is not None:
            raise ValueError("repeat_until requires a repeating schedule")
        if self.repeat_type != RepeatType.NONE and self.repeat_until is not None and self.repeat_until < self.start_datetime:
            raise ValueError("repeat_until must be on or after start_datetime")
        return self


class ScheduleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    category_id: int | None = None
    color: str | None = Field(default=None, max_length=20)
    reminder_minutes: int | None = Field(default=None, ge=0)
    repeat_type: RepeatType | None = None
    repeat_until: datetime | None = None
    completed: bool | None = None


class ScheduleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    start_datetime: datetime
    end_datetime: datetime
    category_id: int | None
    color: str | None
    reminder_minutes: int
    repeat_type: RepeatType
    repeat_until: datetime | None
    completed: bool
    created_at: datetime
    updated_at: datetime
    series_start_datetime: datetime | None = None
    is_recurring_occurrence: bool = False
