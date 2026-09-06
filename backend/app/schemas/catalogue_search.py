from typing import Any

from pydantic import BaseModel, Field


class CatalogueSearchItem(BaseModel):
    show_id: int
    show_title: str
    show_slug: str
    description: str | None = None
    section: str
    categories: list[str] = Field(default_factory=list)
    release_year: int | None = None

    season_number: int
    season_title: str | None = None

    content_group: str
    episode_title: str
    episode_number: int
    episode_description: str | None = None
    duration_seconds: int | None = None
    video_url: str | None = None
    languages: list[str] = Field(default_factory=list)

    artworks: dict[str, str | None] = Field(default_factory=dict)


class CatalogueSearchResponse(BaseModel):
    items: list[CatalogueSearchItem] = Field(default_factory=list)
    total: int
    page: int
    page_size: int
    total_pages: int
    query: str | None = None
    category: str | None = None
    language: str | None = None
    section: str | None = None