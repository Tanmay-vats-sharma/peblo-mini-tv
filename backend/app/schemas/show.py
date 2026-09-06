from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_SECTIONS = {
    "featured",
    "series",
    "minisodes",
    "songs",
}


class ShowBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    section: str | None = None
    categories: list[str] = Field(default_factory=list)
    release_year: int | None = Field(default=None, ge=1900, le=2100)
    is_published: bool = False

    @field_validator("title", "slug")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value

    @field_validator("section")
    @classmethod
    def validate_section(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip().lower()

        if value not in VALID_SECTIONS:
            raise ValueError(
                "Section must be one of: featured, series, minisodes, songs."
            )

        return value

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, value: list[str]) -> list[str]:
        cleaned_categories = []

        for category in value:
            category = category.strip().lower()

            if category and category not in cleaned_categories:
                cleaned_categories.append(category)

        return cleaned_categories


class ShowCreate(ShowBase):
    pass


class ShowUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    section: str | None = None
    categories: list[str] | None = None
    release_year: int | None = Field(default=None, ge=1900, le=2100)
    is_published: bool | None = None

    @field_validator("title", "slug")
    @classmethod
    def validate_optional_text_fields(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty.")

        return value

    @field_validator("section")
    @classmethod
    def validate_optional_section(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip().lower()

        if value not in VALID_SECTIONS:
            raise ValueError(
                "Section must be one of: featured, series, minisodes, songs."
            )

        return value

    @field_validator("categories")
    @classmethod
    def validate_optional_categories(
        cls,
        value: list[str] | None,
    ) -> list[str] | None:
        if value is None:
            return value

        cleaned_categories = []

        for category in value:
            category = category.strip().lower()

            if category and category not in cleaned_categories:
                cleaned_categories.append(category)

        return cleaned_categories


class ShowResponse(ShowBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime