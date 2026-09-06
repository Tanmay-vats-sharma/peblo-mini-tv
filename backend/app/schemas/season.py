from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SeasonBase(BaseModel):
    season_number: int = Field(..., ge=0)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Season title cannot be empty.")

        return value


class SeasonCreate(SeasonBase):
    pass


class SeasonUpdate(BaseModel):
    season_number: int | None = Field(default=None, ge=0)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("Season title cannot be empty.")

        return value


class SeasonResponse(SeasonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    show_id: int
    created_at: datetime
    updated_at: datetime