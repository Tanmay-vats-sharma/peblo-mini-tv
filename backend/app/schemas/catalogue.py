from typing import Any

from pydantic import BaseModel, Field


class CatalogueEpisode(BaseModel):
    content_group: str
    title: str
    episode_number: int
    description: str | None = None
    duration_seconds: int | None = None
    video_url: str | None = None
    languages: list[str] = Field(default_factory=list)


class CatalogueSeason(BaseModel):
    season_number: int
    title: str | None = None
    description: str | None = None
    episodes: list[CatalogueEpisode] = Field(default_factory=list)


class CatalogueShow(BaseModel):
    id: int
    title: str
    slug: str
    description: str | None = None
    section: str
    categories: list[str] = Field(default_factory=list)
    release_year: int | None = None
    artworks: dict[str, str | None] = Field(default_factory=dict)
    seasons: list[CatalogueSeason] = Field(default_factory=list)


class CatalogueSection(BaseModel):
    section: str
    shows: list[CatalogueShow] = Field(default_factory=list)


class CatalogueDocument(BaseModel):
    generated_at: str
    version: int
    sections: list[CatalogueSection] = Field(default_factory=list)


class PublishResponse(BaseModel):
    valid: bool
    status: str
    message: str
    catalogue_path: str | None = None
    version: int | None = None
    show_count: int = 0
    episode_count: int = 0
    error_count: int = 0
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[dict[str, Any]] = Field(default_factory=list)