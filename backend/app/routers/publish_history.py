from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models.publish_run import PublishRun
from app.schemas.publish_history import PublishHistoryResponse

router = APIRouter(
    prefix="/admin/catalog",
    tags=["Catalogue History"],
)


@router.get(
    "/publish-history",
    response_model=list[PublishHistoryResponse],
)
def get_publish_history(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "editor")),
):
    statement = select(PublishRun).order_by(
        PublishRun.started_at.desc(),
        PublishRun.id.desc(),
    )

    return list(db.scalars(statement).all())