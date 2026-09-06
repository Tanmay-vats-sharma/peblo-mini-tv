from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.schemas.catalogue import PublishResponse
from app.schemas.catalogue_search import CatalogueSearchResponse
from app.services.catalogue_service import (
    publish_catalogue,
    read_published_catalogue,
    search_published_catalogue,
)


router = APIRouter(tags=["Catalogue"])


@router.post(
    "/admin/catalog/publish",
    response_model=PublishResponse,
)
def publish_catalogue_endpoint(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin")),
):
    return publish_catalogue(
        db,
        triggered_by=current_user.id,
    )


@router.get("/catalog")
def get_catalogue():
    return read_published_catalogue()


@router.get(
    "/catalog/search",
    response_model=CatalogueSearchResponse,
)
def search_catalogue(
    q: str | None = Query(
        default=None,
        description="Search show and episode text",
    ),
    category: str | None = Query(
        default=None,
        description="Filter by show category",
    ),
    language: str | None = Query(
        default=None,
        description="Filter by language, such as en or hi",
    ),
    section: str | None = Query(
        default=None,
        description="Filter by section",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of results per page",
    ),
):
    return search_published_catalogue(
        query=q,
        category=category,
        language=language,
        section=section,
        page=page,
        page_size=page_size,
    )