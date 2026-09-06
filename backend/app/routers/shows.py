from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models import Show
from app.schemas.show import ShowCreate, ShowResponse, ShowUpdate

router = APIRouter(
    prefix="/admin/shows",
    tags=["Admin Shows"],
    dependencies=[Depends(require_roles("admin", "editor"))],
)


@router.post(
    "",
    response_model=ShowResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_show(
    payload: ShowCreate,
    db: Session = Depends(get_db),
):
    existing_show = db.scalar(
        select(Show).where(
            (Show.slug == payload.slug) | (Show.title == payload.title)
        )
    )

    if existing_show:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A show with this title or slug already exists.",
        )

    if payload.is_published and not payload.section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A published show must have a section.",
        )

    show = Show(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        section=payload.section,
        categories=payload.categories,
        release_year=payload.release_year,
        is_published=payload.is_published,
    )

    db.add(show)

    try:
        db.commit()
        db.refresh(show)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A show with this slug already exists.",
        )

    return show


@router.get(
    "",
    response_model=list[ShowResponse],
)
def list_shows(
    search: str | None = Query(default=None),
    section: str | None = Query(default=None),
    is_published: bool | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Show).order_by(Show.title.asc())

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.where(Show.title.ilike(search_pattern))

    if section:
        query = query.where(Show.section == section.strip().lower())

    if is_published is not None:
        query = query.where(Show.is_published == is_published)

    query = query.offset(skip).limit(limit)

    shows = db.scalars(query).all()

    return shows


@router.get(
    "/{show_id}",
    response_model=ShowResponse,
)
def get_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    return show


@router.patch(
    "/{show_id}",
    response_model=ShowResponse,
)
def update_show(
    show_id: int,
    payload: ShowUpdate,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    new_title = update_data.get("title")
    new_slug = update_data.get("slug")
    new_section = update_data.get("section")
    new_published_status = update_data.get("is_published")

    if new_title is not None and new_title != show.title:
        duplicate_title = db.scalar(
            select(Show).where(
                (Show.title == new_title) & (Show.id != show_id)
            )
        )

        if duplicate_title:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A show with this title already exists.",
            )

    if new_slug is not None and new_slug != show.slug:
        duplicate_slug = db.scalar(
            select(Show).where(
                (Show.slug == new_slug) & (Show.id != show_id)
            )
        )

        if duplicate_slug:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A show with this slug already exists.",
            )

    final_section = (
        new_section if "section" in update_data else show.section
    )

    final_published_status = (
        new_published_status
        if "is_published" in update_data
        else show.is_published
    )

    if final_published_status and not final_section:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A published show must have a section.",
        )

    for field, value in update_data.items():
        setattr(show, field, value)

    try:
        db.commit()
        db.refresh(show)
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A show with this slug already exists.",
        )

    return show


@router.delete(
    "/{show_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_show(
    show_id: int,
    db: Session = Depends(get_db),
):
    show = db.get(Show, show_id)

    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    db.delete(show)
    db.commit()

    return None