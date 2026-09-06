from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.artwork import Artwork, ArtworkType
from app.models.episode import Episode
from app.models.season import Season
from app.models.show import Show
from app.schemas.validation import ValidationIssue, ValidationReport


ALLOWED_SECTIONS = {
    "featured",
    "series",
    "minisodes",
    "songs",
}

ALLOWED_LANGUAGES = {
    "en",
    "hi",
}

ALLOWED_STATUSES = {
    "draft",
    "published",
}

REQUIRED_ARTWORK_TYPES = {
    ArtworkType.POSTER,
    ArtworkType.BANNER,
    ArtworkType.THUMBNAIL,
}

ARTWORK_REQUIREMENTS = {
    ArtworkType.POSTER: {
        "width": 600,
        "height": 900,
        "max_size": 200 * 1024,
    },
    ArtworkType.BANNER: {
        "width": 1280,
        "height": 720,
        "max_size": 200 * 1024,
    },
    ArtworkType.THUMBNAIL: {
        "width": 640,
        "height": 360,
        "max_size": 200 * 1024,
    },
}


def issue(
    code: str,
    message: str,
    entity_type: str,
    entity_id: int | None = None,
    field: str | None = None,
    details: dict[str, object] | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        message=message,
        entity_type=entity_type,
        entity_id=entity_id,
        field=field,
        details=details or {},
    )


def validate_catalogue(db: Session) -> ValidationReport:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    shows = db.scalars(
        select(Show)
        .options(
            selectinload(Show.seasons)
            .selectinload(Season.episodes),
            selectinload(Show.artworks),
        )
        .order_by(Show.id.asc())
    ).all()

    content_group_language_map: dict[
        tuple[str, str],
        list[Episode],
    ] = defaultdict(list)

    for show in shows:
        validate_show(
            show=show,
            errors=errors,
            warnings=warnings,
        )

        artwork_by_type = {
            artwork.artwork_type: artwork
            for artwork in show.artworks
        }

        if show.is_published:
            for artwork_type in REQUIRED_ARTWORK_TYPES:
                if artwork_type not in artwork_by_type:
                    errors.append(
                        issue(
                            code="MISSING_REQUIRED_ARTWORK",
                            message=(
                                f"Published show is missing "
                                f"{artwork_type.value.lower()} artwork"
                            ),
                            entity_type="show",
                            entity_id=show.id,
                            field="artworks",
                            details={
                                "artwork_type": artwork_type.value.lower(),
                            },
                        )
                    )

        for artwork in show.artworks:
            validate_artwork(
                artwork=artwork,
                errors=errors,
                warnings=warnings,
            )

        for season in show.seasons:
            validate_season(
                season=season,
                show=show,
                errors=errors,
                warnings=warnings,
            )

            for episode in season.episodes:
                content_group_language_map[
                    (episode.content_group, episode.language)
                ].append(episode)

                validate_episode(
                    episode=episode,
                    show=show,
                    season=season,
                    errors=errors,
                    warnings=warnings,
                )

    for (
        content_group,
        language,
    ), episodes in content_group_language_map.items():
        if len(episodes) <= 1:
            continue

        errors.append(
            issue(
                code="DUPLICATE_CONTENT_GROUP_LANGUAGE",
                message=(
                    "Multiple episodes use the same "
                    "content_group and language"
                ),
                entity_type="episode",
                details={
                    "content_group": content_group,
                    "language": language,
                    "episode_ids": [
                        episode.id
                        for episode in episodes
                    ],
                    "titles": [
                        episode.title
                        for episode in episodes
                    ],
                },
            )
        )

    return ValidationReport(
        valid=len(errors) == 0,
        error_count=len(errors),
        warning_count=len(warnings),
        errors=errors,
        warnings=warnings,
    )


def validate_show(
    show: Show,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    if not show.title.strip():
        errors.append(
            issue(
                code="EMPTY_SHOW_TITLE",
                message="Show title cannot be empty",
                entity_type="show",
                entity_id=show.id,
                field="title",
            )
        )

    if show.section is None:
        if show.is_published:
            errors.append(
                issue(
                    code="PUBLISHED_SHOW_MISSING_SECTION",
                    message="Published show must have a section",
                    entity_type="show",
                    entity_id=show.id,
                    field="section",
                )
            )
        else:
            warnings.append(
                issue(
                    code="DRAFT_SHOW_MISSING_SECTION",
                    message="Draft show does not have a section",
                    entity_type="show",
                    entity_id=show.id,
                    field="section",
                )
            )

    elif show.section not in ALLOWED_SECTIONS:
        errors.append(
            issue(
                code="INVALID_SHOW_SECTION",
                message=f"Invalid show section: {show.section}",
                entity_type="show",
                entity_id=show.id,
                field="section",
                details={
                    "allowed_sections": sorted(ALLOWED_SECTIONS),
                },
            )
        )


def validate_season(
    season: Season,
    show: Show,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    if season.season_number < 0:
        errors.append(
            issue(
                code="INVALID_SEASON_NUMBER",
                message="Season number cannot be negative",
                entity_type="season",
                entity_id=season.id,
                field="season_number",
                details={
                    "show_id": show.id,
                    "season_number": season.season_number,
                },
            )
        )

    if season.season_number == 0:
        warnings.append(
            issue(
                code="TRAILER_SEASON",
                message=(
                    "Season 0 is reserved for trailers and will not "
                    "appear as a normal viewer season"
                ),
                entity_type="season",
                entity_id=season.id,
                field="season_number",
                details={
                    "show_id": show.id,
                },
            )
        )


def validate_episode(
    episode: Episode,
    show: Show,
    season: Season,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    if episode.language not in ALLOWED_LANGUAGES:
        errors.append(
            issue(
                code="INVALID_EPISODE_LANGUAGE",
                message=f"Invalid episode language: {episode.language}",
                entity_type="episode",
                entity_id=episode.id,
                field="language",
                details={
                    "allowed_languages": sorted(ALLOWED_LANGUAGES),
                },
            )
        )

    if episode.status not in ALLOWED_STATUSES:
        errors.append(
            issue(
                code="INVALID_EPISODE_STATUS",
                message=f"Invalid episode status: {episode.status}",
                entity_type="episode",
                entity_id=episode.id,
                field="status",
            )
        )

    if episode.episode_number < 0:
        errors.append(
            issue(
                code="INVALID_EPISODE_NUMBER",
                message="Episode number cannot be negative",
                entity_type="episode",
                entity_id=episode.id,
                field="episode_number",
            )
        )

    if not episode.content_group.strip():
        errors.append(
            issue(
                code="MISSING_CONTENT_GROUP",
                message="Episode content_group is required",
                entity_type="episode",
                entity_id=episode.id,
                field="content_group",
            )
        )

    if episode.status == "published":
        if episode.duration_seconds is None:
            errors.append(
                issue(
                    code="PUBLISHED_EPISODE_MISSING_DURATION",
                    message="Published episode must have a duration",
                    entity_type="episode",
                    entity_id=episode.id,
                    field="duration_seconds",
                    details={
                        "show_id": show.id,
                        "season_id": season.id,
                    },
                )
            )
        elif episode.duration_seconds <= 0:
            errors.append(
                issue(
                    code="INVALID_EPISODE_DURATION",
                    message="Episode duration must be positive",
                    entity_type="episode",
                    entity_id=episode.id,
                    field="duration_seconds",
                )
            )

        if not episode.video_url:
            errors.append(
                issue(
                    code="PUBLISHED_EPISODE_MISSING_VIDEO",
                    message="Published episode must have a video URL",
                    entity_type="episode",
                    entity_id=episode.id,
                    field="video_url",
                    details={
                        "show_id": show.id,
                        "season_id": season.id,
                    },
                )
            )


def validate_artwork(
    artwork: Artwork,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    requirements = ARTWORK_REQUIREMENTS.get(artwork.artwork_type)

    if requirements is None:
        errors.append(
            issue(
                code="INVALID_ARTWORK_TYPE",
                message="Artwork type is not supported",
                entity_type="artwork",
                entity_id=artwork.id,
                field="artwork_type",
            )
        )
        return

    expected_width = requirements["width"]
    expected_height = requirements["height"]
    max_size = requirements["max_size"]

    if (
        artwork.width != expected_width
        or artwork.height != expected_height
    ):
        errors.append(
            issue(
                code="INVALID_ARTWORK_DIMENSIONS",
                message=(
                    f"Artwork must be exactly "
                    f"{expected_width}x{expected_height}"
                ),
                entity_type="artwork",
                entity_id=artwork.id,
                field="width",
                details={
                    "actual_width": artwork.width,
                    "actual_height": artwork.height,
                    "expected_width": expected_width,
                    "expected_height": expected_height,
                },
            )
        )

    if artwork.file_size_bytes > max_size:
        errors.append(
            issue(
                code="ARTWORK_TOO_LARGE",
                message="Artwork file size must not exceed 200 KB",
                entity_type="artwork",
                entity_id=artwork.id,
                field="file_size_bytes",
                details={
                    "file_size_bytes": artwork.file_size_bytes,
                    "max_size_bytes": max_size,
                },
            )
        )

    if not artwork.storage_key:
        errors.append(
            issue(
                code="MISSING_ARTWORK_STORAGE_KEY",
                message="Artwork is missing its storage key",
                entity_type="artwork",
                entity_id=artwork.id,
                field="storage_key",
            )
        )