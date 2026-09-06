from __future__ import annotations

import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.artwork import ArtworkType
from app.models.episode import Episode
from app.models.season import Season
from app.models.show import Show
from app.schemas.catalogue import (
    CatalogueDocument,
    CatalogueEpisode,
    CatalogueSection,
    CatalogueSeason,
    CatalogueShow,
)
from app.services.catalogue_validation import validate_catalogue


SECTION_ORDER = {
    "featured": 0,
    "series": 1,
    "minisodes": 2,
    "songs": 3,
}

BACKEND_DIR = Path(__file__).resolve().parents[2]
CATALOGUE_DIR = BACKEND_DIR / "catalogue"
LIVE_CATALOGUE_PATH = CATALOGUE_DIR / "catalogue.json"


def _artwork_url(show: Show, artwork_type: ArtworkType) -> str | None:
    """
    Return the public URL for one artwork type.

    The database stores the relative image URL. The viewer can use
    this URL directly when the API and frontend are served together.
    """
    for artwork in show.artworks:
        if artwork.artwork_type == artwork_type:
            return artwork.image_url

    return None


def _episode_to_catalogue(
    episodes: list[Episode],
) -> CatalogueEpisode:
    """
    Convert language variants belonging to one content_group into
    a single catalogue episode.

    The first episode provides the common metadata. Languages from
    all variants are combined and sorted.
    """
    ordered_episodes = sorted(
        episodes,
        key=lambda episode: (
            episode.episode_number,
            episode.language,
            episode.id,
        ),
    )

    first_episode = ordered_episodes[0]

    languages = sorted(
        {
            episode.language
            for episode in ordered_episodes
            if episode.language
        }
    )

    # Prefer the English variant for common display metadata when it exists.
    display_episode = next(
        (
            episode
            for episode in ordered_episodes
            if episode.language == "en"
        ),
        first_episode,
    )

    return CatalogueEpisode(
        content_group=display_episode.content_group,
        title=display_episode.title,
        episode_number=display_episode.episode_number,
        description=display_episode.description,
        duration_seconds=display_episode.duration_seconds,
        video_url=display_episode.video_url,
        languages=languages,
    )


def build_catalogue(db: Session) -> CatalogueDocument:
    """
    Build a deterministic catalogue from published database records.

    Season 0 is excluded because it is reserved for trailers.
    """
    shows = db.scalars(
        select(Show)
        .options(
            selectinload(Show.artworks),
            selectinload(Show.seasons)
            .selectinload(Season.episodes),
        )
        .where(
            Show.is_published.is_(True),
            Show.section.is_not(None),
        )
    ).all()

    grouped_sections: dict[str, list[CatalogueShow]] = defaultdict(list)

    for show in shows:
        if not show.section:
            continue

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

            grouped_episodes: dict[str, list[Episode]] = defaultdict(list)

            for episode in published_episodes:
                grouped_episodes[episode.content_group].append(episode)

            catalogue_episodes = [
                _episode_to_catalogue(episode_group)
                for episode_group in grouped_episodes.values()
            ]

            catalogue_episodes.sort(
                key=lambda episode: (
                    episode.episode_number,
                    episode.title.casefold(),
                    episode.content_group,
                )
            )

            if not catalogue_episodes:
                continue

            catalogue_seasons.append(
                CatalogueSeason(
                    season_number=season.season_number,
                    title=season.title,
                    description=season.description,
                    episodes=catalogue_episodes,
                )
            )

        if not catalogue_seasons:
            continue

        catalogue_show = CatalogueShow(
            id=show.id,
            title=show.title,
            slug=show.slug,
            description=show.description,
            section=show.section,
            categories=show.categories or [],
            release_year=show.release_year,
            artworks={
                "poster": _artwork_url(show, ArtworkType.POSTER),
                "banner": _artwork_url(show, ArtworkType.BANNER),
                "thumbnail": _artwork_url(show, ArtworkType.THUMBNAIL),
            },
            seasons=catalogue_seasons,
        )

        grouped_sections[show.section].append(catalogue_show)

    sections: list[CatalogueSection] = []

    for section_name in sorted(
        grouped_sections,
        key=lambda section: SECTION_ORDER.get(section, 999),
    ):
        shows_in_section = sorted(
            grouped_sections[section_name],
            key=lambda show: (
                show.title.casefold(),
                show.id,
            ),
        )

        sections.append(
            CatalogueSection(
                section=section_name,
                shows=shows_in_section,
            )
        )

    return CatalogueDocument(
        generated_at=datetime.now(timezone.utc).isoformat(),
        version=1,
        sections=sections,
    )


def _write_json_atomically(
    document: CatalogueDocument,
    destination: Path,
) -> None:
    """
    Write JSON to a temporary file in the same directory, flush it,
    then atomically replace the live file.

    os.replace() ensures readers see either the old complete file
    or the new complete file, never a partially written file.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix="catalogue-",
        suffix=".json.tmp",
        dir=destination.parent,
        text=True,
    )

    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(
            file_descriptor,
            "w",
            encoding="utf-8",
        ) as temporary_file:
            json.dump(
                document.model_dump(mode="json"),
                temporary_file,
                indent=2,
                ensure_ascii=False,
            )
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())

        os.replace(temporary_path, destination)

    except Exception:
        if temporary_path.exists():
            temporary_path.unlink()
        raise


def publish_catalogue(db: Session) -> dict[str, Any]:
    """
    Validate and publish the catalogue.

    Publishing is blocked when validation contains errors.
    """
    report = validate_catalogue(db)

    report_errors = [
        error.model_dump()
        for error in report.errors
    ]

    report_warnings = [
        warning.model_dump()
        for warning in report.warnings
    ]

    if not report.valid:
        return {
            "valid": False,
            "status": "blocked",
            "message": "Catalogue publishing blocked because validation failed",
            "catalogue_path": None,
            "version": None,
            "show_count": 0,
            "episode_count": 0,
            "error_count": report.error_count,
            "errors": report_errors,
            "warnings": report_warnings,
        }

    document = build_catalogue(db)

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

    _write_json_atomically(
        document=document,
        destination=LIVE_CATALOGUE_PATH,
    )

    return {
        "valid": True,
        "status": "succeeded",
        "message": "Catalogue published successfully",
        "catalogue_path": str(LIVE_CATALOGUE_PATH),
        "version": document.version,
        "show_count": show_count,
        "episode_count": episode_count,
        "error_count": 0,
        "errors": [],
        "warnings": report_warnings,
    }


def read_published_catalogue() -> dict[str, Any]:
    """
    Read the last successfully published catalogue.
    """
    if not LIVE_CATALOGUE_PATH.exists():
        return {
            "message": "No published catalogue exists"
        }

    with LIVE_CATALOGUE_PATH.open(
        "r",
        encoding="utf-8",
    ) as catalogue_file:
        return json.load(catalogue_file)