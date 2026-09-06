from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.schemas.validation import ValidationReport
from app.services.catalogue_validation import validate_catalogue

router = APIRouter(
    prefix="/admin",
    tags=["Validation"],
)


@router.get(
    "/validation-report",
    response_model=ValidationReport,
)
def get_validation_report(
    db: Session = Depends(get_db),
    _current_user=Depends(require_roles("admin", "editor")),
):
    return validate_catalogue(db)