from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_roles
from app.models import Artwork, ArtworkType, Show
from app.services.artwork_service import validate_and_save_artwork


router = APIRouter(
    prefix="/admin/artworks",
    tags=["Admin Artwork"],
    dependencies=[Depends(require_roles("admin", "editor"))],
)

BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIRECTORY = BASE_DIR / "storage" / "artworks"

ALLOWED_ARTWORK_TYPES = {
    "poster": ArtworkType.POSTER,
    "banner": ArtworkType.BANNER,
    "thumbnail": ArtworkType.THUMBNAIL,
}


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
)
async def upload_artwork(
    show_id: int = Form(...),
    artwork_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    artwork_type = artwork_type.strip().lower()

    if artwork_type not in ALLOWED_ARTWORK_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Invalid artwork_type. "
                "Allowed values: poster, banner, thumbnail."
            ),
        )

    artwork_type_enum = ALLOWED_ARTWORK_TYPES[artwork_type]

    show = db.scalar(
        select(Show).where(Show.id == show_id)
    )

    if show is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Show not found.",
        )

    validated_artwork = await validate_and_save_artwork(
        file=file,
        artwork_type=artwork_type,
        storage_directory=STORAGE_DIRECTORY,
    )

    existing_artwork = db.scalar(
        select(Artwork).where(
            Artwork.show_id == show_id,
            Artwork.artwork_type == artwork_type_enum,
        )
    )

    old_storage_key = None

    try:
        if existing_artwork:
            old_storage_key = existing_artwork.storage_key

            existing_artwork.original_filename = (
                validated_artwork.original_filename
            )
            existing_artwork.storage_key = (
                validated_artwork.storage_key
            )
            existing_artwork.image_url = (
                f"/storage/{validated_artwork.storage_key}"
            )
            existing_artwork.mime_type = (
                validated_artwork.mime_type
            )
            existing_artwork.width = validated_artwork.width
            existing_artwork.height = validated_artwork.height
            existing_artwork.file_size_bytes = (
                validated_artwork.file_size_bytes
            )

            artwork = existing_artwork

        else:
            artwork = Artwork(
                show_id=show_id,
                artwork_type=artwork_type_enum,
                original_filename=(
                    validated_artwork.original_filename
                ),
                storage_key=validated_artwork.storage_key,
                image_url=(
                    f"/storage/{validated_artwork.storage_key}"
                ),
                mime_type=validated_artwork.mime_type,
                width=validated_artwork.width,
                height=validated_artwork.height,
                file_size_bytes=(
                    validated_artwork.file_size_bytes
                ),
            )

            db.add(artwork)

        db.commit()
        db.refresh(artwork)

    except Exception:
        db.rollback()

        new_file_path = (
            BASE_DIR
            / "storage"
            / validated_artwork.storage_key
        )

        if new_file_path.exists():
            new_file_path.unlink()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Artwork upload failed. Database changes were rolled back.",
        )

    # Delete the old file only after the database commit succeeds.
    if old_storage_key:
        old_file_path = (
            BASE_DIR / "storage" / old_storage_key
        )

        if old_file_path.exists():
            old_file_path.unlink()

    return {
        "success": True,
        "message": "Artwork uploaded successfully.",
        "artwork": {
            "id": artwork.id,
            "show_id": artwork.show_id,
            "artwork_type": artwork.artwork_type.value,
            "original_filename": artwork.original_filename,
            "storage_key": artwork.storage_key,
            "image_url": artwork.image_url,
            "mime_type": artwork.mime_type,
            "width": artwork.width,
            "height": artwork.height,
            "file_size_bytes": artwork.file_size_bytes,
        },
    }