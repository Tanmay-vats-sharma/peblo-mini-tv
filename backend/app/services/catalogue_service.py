from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.publish_run import PublishRun, PublishRunStatus
from app.models.show import Show
from app.schemas.catalogue import (
    CatalogueDocument,
    CatalogueEpisode,
    CatalogueSection,
    CatalogueSeason,
    CatalogueShow,
    PublishResponse,
)
from app.services.catalogue_validation import validate_catalogue


SECTION_ORDER = [
    "featured",
    "series",
    "minisodes",
    "songs",
]

BACKEND_DIR = Path(__file__).resolve().parents[2]
CATALOGUE_DIR = BACKEND_DIR / "catalogue"
CATALOGUE_PATH = CATALOGUE_DIR / "catalogue.json"


def _artwork_url(artwork: Any) -> str | None:
    """
    Return the public URL for an artwork record.
    """

    if artwork is None:
        return None

    if artwork.image_url:
        return artwork.image_url

    if artwork.storage_key:
        return f"/storage/{artwork.storage_key}"

    return None


def _episode_to_catalogue(
    episodes: list[Any],
) -> CatalogueEpisode:
    """
    Collapse language variants with the same content_group
    into one catalogue episode.

    English is preferred as the primary episode when available.
    """

    ordered_episodes = sorted(
        episodes,
        key=lambda episode: (
            episode.language != "en",
            episode.id,
        ),
    )

    primary_episode = ordered_episodes[0]

    languages = sorted(
        {
            episode.language
            for episode in episodes
            if episode.language
        }
    )

    return CatalogueEpisode(
        content_group=primary_episode.content_group,
        title=primary_episode.title,
        episode_number=primary_episode.episode_number,
        description=primary_episode.description,
        duration_seconds=primary_episode.duration_seconds,
        video_url=primary_episode.video_url,
        languages=languages,
    )


def build_catalogue(
    db: Session,
    version: int,
) -> CatalogueDocument:
    """
    Build the public catalogue from published database records only.

    Rules:
    - Only published shows are included.
    - Shows without a section are skipped.
    - Season 0 is hidden because it is reserved for trailers.
    - Only published episodes are included.
    - Episodes with the same content_group are collapsed.
    - Sections follow the required order.
    - Shows are sorted alphabetically.
    - Seasons and episodes are sorted numerically.
    """

    statement = (
        select(Show)
        .where(Show.is_published.is_(True))
        .options(
            selectinload(Show.seasons).selectinload(
                Show.seasons.property.mapper.class_.episodes
            ),
            selectinload(Show.artworks),
        )
        .order_by(
            Show.title.asc(),
            Show.id.asc(),
        )
    )

    shows = list(
        db.scalars(statement).unique().all()
    )

    sections: dict[str, list[CatalogueShow]] = {
        section: []
        for section in SECTION_ORDER
    }

    for show in shows:
        if not show.section:
            continue

        artwork_map = {
            artwork.artwork_type.value.lower(): _artwork_url(
                artwork
            )
            for artwork in show.artworks
        }

        catalogue_seasons: list[CatalogueSeason] = []

        for season in sorted(
            show.seasons,
            key=lambda item: item.season_number,
        ):
            # Season 0 is reserved for trailers.
            if season.season_number == 0:
                continue

            published_episodes = [
                episode
                for episode in season.episodes
                if episode.status == "published"
            ]

            grouped_episodes: dict[str, list[Any]] = {}

            for episode in published_episodes:
                grouped_episodes.setdefault(
                    episode.content_group,
                    [],
                ).append(episode)

            catalogue_episodes = [
                _episode_to_catalogue(group)
                for group in grouped_episodes.values()
            ]

            catalogue_episodes.sort(
                key=lambda episode: (
                    episode.episode_number,
                    episode.content_group,
                )
            )

            catalogue_seasons.append(
                CatalogueSeason(
                    season_number=season.season_number,
                    title=season.title,
                    description=season.description,
                    episodes=catalogue_episodes,
                )
            )

        catalogue_show = CatalogueShow(
            id=show.id,
            title=show.title,
            slug=show.slug,
            description=show.description,
            section=show.section,
            categories=show.categories or [],
            release_year=show.release_year,
            artworks=artwork_map,
            seasons=catalogue_seasons,
        )

        sections[show.section].append(
            catalogue_show
        )

    for section in SECTION_ORDER:
        sections[section].sort(
            key=lambda show: (
                show.title.casefold(),
                show.id,
            )
        )

    return CatalogueDocument(
        generated_at=datetime.now(
            timezone.utc
        ).isoformat(),
        version=version,
        sections=[
            CatalogueSection(
                section=section,
                shows=sections[section],
            )
            for section in SECTION_ORDER
        ],
    )


def _write_json_atomically(
    document: CatalogueDocument,
) -> None:
    """
    Write the catalogue to a temporary file first.

    The live catalogue.json is replaced only after the temporary
    file has been completely written and flushed to disk.
    """

    CATALOGUE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = document.model_dump_json(
        indent=2,
    )

    temporary_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=CATALOGUE_DIR,
            prefix="catalogue-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_file.write(payload)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
            temporary_path = temporary_file.name

        os.replace(
            temporary_path,
            CATALOGUE_PATH,
        )

    finally:
        if (
            temporary_path
            and os.path.exists(temporary_path)
        ):
            os.remove(temporary_path)


def _validation_items(
    report: Any,
) -> tuple[list[dict], list[dict]]:
    """
    Convert validation issues into response dictionaries.
    """

    errors = [
        issue.model_dump()
        for issue in report.errors
    ]

    warnings = [
        issue.model_dump()
        for issue in report.warnings
    ]

    return errors, warnings


def publish_catalogue(
    db: Session,
    triggered_by: int | None = None,
) -> PublishResponse:
    """
    Validate and publish the catalogue.

    Every publish attempt is recorded in publish_runs.

    triggered_by stores the ID of the authenticated admin
    who initiated the publish operation.
    """

    publish_run = PublishRun(
        triggered_by=triggered_by,
        status=PublishRunStatus.PENDING.value,
        message="Catalogue publishing started",
    )

    db.add(publish_run)
    db.flush()

    try:
        report = validate_catalogue(db)

        errors, warnings = _validation_items(report)

        publish_run.error_count = report.error_count
        publish_run.completed_at = datetime.now(
            timezone.utc
        )

        if not report.valid:
            publish_run.status = (
                PublishRunStatus.BLOCKED.value
            )

            publish_run.message = (
                "Catalogue publishing blocked because "
                "validation failed"
            )

            db.commit()

            return PublishResponse(
                valid=False,
                status="blocked",
                message=publish_run.message,
                catalogue_path=None,
                version=None,
                show_count=0,
                episode_count=0,
                error_count=report.error_count,
                errors=errors,
                warnings=warnings,
            )

        # The publish run ID provides a unique catalogue version.
        next_version = publish_run.id

        document = build_catalogue(
            db,
            version=next_version,
        )

        # Replace the live file only after the complete document
        # has been successfully written.
        _write_json_atomically(document)

        show_count = sum(
            len(section.shows)
            for section in document.sections
        )

        episode_count = sum(
            len(season.episodes)
            for section in document.sections
            for show in section.shows
            for season in show.seasons
        )

        publish_run.status = (
            PublishRunStatus.SUCCEEDED.value
        )

        publish_run.catalogue_path = str(
            CATALOGUE_PATH
        )

        publish_run.show_count = show_count
        publish_run.episode_count = episode_count
        publish_run.error_count = 0
        publish_run.message = (
            "Catalogue published successfully"
        )
        publish_run.completed_at = datetime.now(
            timezone.utc
        )

        db.commit()

        return PublishResponse(
            valid=True,
            status="succeeded",
            message=publish_run.message,
            catalogue_path=str(CATALOGUE_PATH),
            version=next_version,
            show_count=show_count,
            episode_count=episode_count,
            error_count=0,
            errors=[],
            warnings=warnings,
        )

    except Exception as exc:
        db.rollback()

        return PublishResponse(
            valid=False,
            status="failed",
            message=f"Catalogue publishing failed: {exc}",
            catalogue_path=None,
            version=None,
            show_count=0,
            episode_count=0,
            error_count=0,
            errors=[],
            warnings=[],
        )


def read_published_catalogue() -> dict[str, Any]:
    """
    Read the currently published catalogue.

    If no catalogue has been published yet, return a clear message.
    """

    if not CATALOGUE_PATH.exists():
        return {
            "message": "No published catalogue exists",
        }

    with CATALOGUE_PATH.open(
        "r",
        encoding="utf-8",
    ) as catalogue_file:
        return json.load(catalogue_file)


def search_published_catalogue(
    *,
    query: str | None = None,
    category: str | None = None,
    language: str | None = None,
    section: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    Search the published catalogue file.

    The public viewer searches catalogue.json rather than
    draft database records.
    """

    catalogue = read_published_catalogue()

    if (
        "message" in catalogue
        and "sections" not in catalogue
    ):
        return {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0,
            "query": query,
            "category": category,
            "language": language,
            "section": section,
        }

    normalized_query = (
        query.strip().lower()
        if query
        else None
    )

    normalized_category = (
        category.strip().lower()
        if category
        else None
    )

    normalized_language = (
        language.strip().lower()
        if language
        else None
    )

    normalized_section = (
        section.strip().lower()
        if section
        else None
    )

    results: list[dict] = []

    for catalogue_section in catalogue.get(
        "sections",
        [],
    ):
        current_section = str(
            catalogue_section.get(
                "section",
                "",
            )
        ).lower()

        if (
            normalized_section
            and current_section != normalized_section
        ):
            continue

        for show in catalogue_section.get(
            "shows",
            [],
        ):
            show_title = str(
                show.get("title", "")
            )

            show_description = str(
                show.get("description") or ""
            )

            show_categories = [
                str(item).lower()
                for item in show.get(
                    "categories",
                    [],
                )
            ]

            if normalized_category:
                if normalized_category not in show_categories:
                    continue

            for season in show.get(
                "seasons",
                [],
            ):
                for episode in season.get(
                    "episodes",
                    [],
                ):
                    episode_title = str(
                        episode.get("title", "")
                    )

                    episode_description = str(
                        episode.get("description") or ""
                    )

                    episode_languages = [
                        str(item).lower()
                        for item in episode.get(
                            "languages",
                            [],
                        )
                    ]

                    if normalized_language:
                        if (
                            normalized_language
                            not in episode_languages
                        ):
                            continue

                    if normalized_query:
                        searchable_text = " ".join(
                            [
                                show_title,
                                show_description,
                                episode_title,
                                episode_description,
                                *show_categories,
                            ]
                        ).lower()

                        if (
                            normalized_query
                            not in searchable_text
                        ):
                            continue

                    results.append(
                        {
                            "show_id": show["id"],
                            "show_title": show_title,
                            "show_slug": show["slug"],
                            "description": show.get(
                                "description"
                            ),
                            "section": current_section,
                            "categories": show.get(
                                "categories",
                                [],
                            ),
                            "release_year": show.get(
                                "release_year"
                            ),
                            "season_number": season[
                                "season_number"
                            ],
                            "season_title": season.get(
                                "title"
                            ),
                            "content_group": episode[
                                "content_group"
                            ],
                            "episode_title": episode_title,
                            "episode_number": episode[
                                "episode_number"
                            ],
                            "episode_description": episode.get(
                                "description"
                            ),
                            "duration_seconds": episode.get(
                                "duration_seconds"
                            ),
                            "video_url": episode.get(
                                "video_url"
                            ),
                            "languages": episode.get(
                                "languages",
                                [],
                            ),
                            "artworks": show.get(
                                "artworks",
                                {},
                            ),
                        }
                    )

    total = len(results)

    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    paginated_items = results[
        start_index:end_index
    ]

    total_pages = (
        (total + page_size - 1) // page_size
        if total > 0
        else 0
    )

    return {
        "items": paginated_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "query": query,
        "category": category,
        "language": language,
        "section": section,
    }