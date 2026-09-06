from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.episode import Episode
from app.models.season import Season
from app.schemas.episode import EpisodeCreate, EpisodeResponse, EpisodeUpdate


router = APIRouter(
    prefix="/admin",
    tags=["Episodes"],
    dependencies=[Depends(require_roles("admin", "editor"))],
)


def validate_published_episode(
    episode_status: str,
    duration_seconds: int | None,
    video_url: str | None,
) -> None:
    """
    Published episodes must have the information required
    by the viewer to play the content.
    """

    if episode_status != "published":
        return

    if duration_seconds is None or duration_seconds <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Published episodes must have a positive duration_seconds",
        )

    if not video_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Published episodes must have a video_url",
        )


def ensure_unique_content_group_language(
    db: Session,
    content_group: str,
    language: str,
    exclude_episode_id: int | None = None,
) -> None:
    """
    One content_group/language pair represents one language version.
    """

    query = select(Episode).where(
        Episode.content_group == content_group,
        Episode.language == language,
    )

    if exclude_episode_id is not None:
        query = query.where(Episode.id != exclude_episode_id)

    existing_episode = db.scalar(query)

    if existing_episode:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "An episode already exists for this "
                "content_group and language"
            ),
        )


@router.post(
    "/seasons/{season_id}/episodes",
    response_model=EpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_episode(
    season_id: int,
    payload: EpisodeCreate,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found",
        )

    ensure_unique_content_group_language(
        db=db,
        content_group=payload.content_group,
        language=payload.language,
    )

    validate_published_episode(
        episode_status=payload.status,
        duration_seconds=payload.duration_seconds,
        video_url=payload.video_url,
    )

    seed_episode_id = payload.seed_episode_id or f"manual-{uuid4()}"

    existing_seed_id = db.scalar(
        select(Episode).where(
            Episode.seed_episode_id == seed_episode_id
        )
    )

    if existing_seed_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="seed_episode_id already exists",
        )

    episode = Episode(
        seed_episode_id=seed_episode_id,
        season_id=season_id,
        title=payload.title,
        episode_number=payload.episode_number,
        content_group=payload.content_group,
        language=payload.language,
        status=payload.status,
        description=payload.description,
        video_url=payload.video_url,
        duration_seconds=payload.duration_seconds,
    )

    db.add(episode)

    try:
        db.commit()
        db.refresh(episode)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Episode could not be created because of a database conflict",
        )

    return episode


@router.get(
    "/seasons/{season_id}/episodes",
    response_model=list[EpisodeResponse],
)
def list_episodes(
    season_id: int,
    language: str | None = Query(default=None),
    episode_status: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if season is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found",
        )

    query = select(Episode).where(
        Episode.season_id == season_id
    )

    if language is not None:
        language = language.strip().lower()

        if language not in {"en", "hi"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Language must be either 'en' or 'hi'",
            )

        query = query.where(Episode.language == language)

    if episode_status is not None:
        episode_status = episode_status.strip().lower()

        if episode_status not in {"draft", "published"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Status must be either 'draft' or 'published'",
            )

        query = query.where(Episode.status == episode_status)

    query = query.order_by(
        Episode.episode_number.asc(),
        Episode.language.asc(),
        Episode.id.asc(),
    )

    return db.scalars(query).all()


@router.get(
    "/episodes/{episode_id}",
    response_model=EpisodeResponse,
)
def get_episode(
    episode_id: int,
    db: Session = Depends(get_db),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found",
        )

    return episode


@router.patch(
    "/episodes/{episode_id}",
    response_model=EpisodeResponse,
)
def update_episode(
    episode_id: int,
    payload: EpisodeUpdate,
    db: Session = Depends(get_db),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found",
        )

    updates = payload.model_dump(exclude_unset=True)

    final_content_group = updates.get(
        "content_group",
        episode.content_group,
    )

    final_language = updates.get(
        "language",
        episode.language,
    )

    final_status = updates.get(
        "status",
        episode.status,
    )

    final_duration = updates.get(
        "duration_seconds",
        episode.duration_seconds,
    )

    final_video_url = updates.get(
        "video_url",
        episode.video_url,
    )

    ensure_unique_content_group_language(
        db=db,
        content_group=final_content_group,
        language=final_language,
        exclude_episode_id=episode.id,
    )

    validate_published_episode(
        episode_status=final_status,
        duration_seconds=final_duration,
        video_url=final_video_url,
    )

    for field_name, field_value in updates.items():
        setattr(episode, field_name, field_value)

    try:
        db.commit()
        db.refresh(episode)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Episode could not be updated because of a database conflict",
        )

    return episode


@router.delete(
    "/episodes/{episode_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_episode(
    episode_id: int,
    db: Session = Depends(get_db),
):
    episode = db.get(Episode, episode_id)

    if episode is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode not found",
        )

    db.delete(episode)
    db.commit()

    return None