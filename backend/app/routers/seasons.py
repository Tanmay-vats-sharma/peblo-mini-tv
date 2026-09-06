from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models import Season, Show
from app.schemas.season import SeasonCreate, SeasonResponse, SeasonUpdate

router = APIRouter(
    prefix="/admin",
    tags=["Admin Seasons"],
    dependencies=[Depends(require_roles("admin", "editor"))],
)


@router.post(
    "/shows/{show_id}/seasons",
    response_model=SeasonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_season(
    show_id: int,
    payload: SeasonCreate,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    existing_season = db.scalar(
        select(Season).where(
            (Season.show_id == show_id)
            & (Season.season_number == payload.season_number)
        )
    )

    if existing_season:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This season number already exists for the show.",
        )

    season = Season(
        show_id=show_id,
        season_number=payload.season_number,
        title=payload.title,
        description=payload.description,
    )

    db.add(season)

    try:
        db.commit()
        db.refresh(season)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This season number already exists for the show.",
        )

    return season


@router.get(
    "/shows/{show_id}/seasons",
    response_model=list[SeasonResponse],
)
def list_seasons(
    show_id: int,
    include_trailers: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    query = select(Season).where(Season.show_id == show_id)

    if not include_trailers:
        query = query.where(Season.season_number != 0)

    query = query.order_by(Season.season_number.asc())

    return db.scalars(query).all()


@router.get(
    "/seasons/{season_id}",
    response_model=SeasonResponse,
)
def get_season(
    season_id: int,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found.",
        )

    return season


@router.patch(
    "/seasons/{season_id}",
    response_model=SeasonResponse,
)
def update_season(
    season_id: int,
    payload: SeasonUpdate,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    new_season_number = update_data.get("season_number")

    if (
        new_season_number is not None
        and new_season_number != season.season_number
    ):
        duplicate_season = db.scalar(
            select(Season).where(
                (Season.show_id == season.show_id)
                & (Season.season_number == new_season_number)
                & (Season.id != season_id)
            )
        )

        if duplicate_season:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This season number already exists for the show.",
            )

    for field, value in update_data.items():
        setattr(season, field, value)

    try:
        db.commit()
        db.refresh(season)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This season number already exists for the show.",
        )

    return season


@router.delete(
    "/seasons/{season_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_season(
    season_id: int,
    db: Session = Depends(get_db),
):
    season = db.get(Season, season_id)

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found.",
        )

    db.delete(season)
    db.commit()

    return None