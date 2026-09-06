from pydantic import BaseModel, ConfigDict, Field, field_validator


ALLOWED_LANGUAGES = {"en", "hi"}
ALLOWED_STATUSES = {"draft", "published"}


class EpisodeBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    episode_number: int = Field(ge=0)
    content_group: str = Field(min_length=1, max_length=255)
    language: str = Field(min_length=2, max_length=10)
    status: str = Field(default="draft", max_length=50)
    description: str | None = None
    video_url: str | None = Field(default=None, max_length=1000)
    duration_seconds: int | None = Field(default=None, gt=0)

    @field_validator("title", "content_group")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in ALLOWED_LANGUAGES:
            raise ValueError("Language must be either 'en' or 'hi'")

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in ALLOWED_STATUSES:
            raise ValueError("Status must be either 'draft' or 'published'")

        return value

    @field_validator("video_url")
    @classmethod
    def normalize_video_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class EpisodeCreate(EpisodeBase):
    seed_episode_id: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


class EpisodeUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    episode_number: int | None = Field(default=None, ge=0)
    content_group: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    language: str | None = Field(default=None, min_length=2, max_length=10)
    status: str | None = Field(default=None, max_length=50)
    description: str | None = None
    video_url: str | None = Field(default=None, max_length=1000)
    duration_seconds: int | None = Field(default=None, gt=0)

    @field_validator("title", "content_group")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("This field cannot be empty")

        return value

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()

        if value not in ALLOWED_LANGUAGES:
            raise ValueError("Language must be either 'en' or 'hi'")

        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()

        if value not in ALLOWED_STATUSES:
            raise ValueError("Status must be either 'draft' or 'published'")

        return value

    @field_validator("video_url")
    @classmethod
    def normalize_video_url(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class EpisodeResponse(EpisodeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    seed_episode_id: str
    season_id: int