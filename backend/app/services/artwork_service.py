from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError


MAX_FILE_SIZE_BYTES = 200 * 1024

ARTWORK_RULES = {
    "poster": {
        "target_width": 600,
        "target_height": 900,
        "ratio": 2 / 3,
    },
    "banner": {
        "target_width": 1280,
        "target_height": 720,
        "ratio": 16 / 9,
    },
    "thumbnail": {
        "target_width": 640,
        "target_height": 360,
        "ratio": 16 / 9,
    },
}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@dataclass
class ValidatedArtwork:
    original_filename: str
    storage_key: str
    mime_type: str
    width: int
    height: int
    file_size_bytes: int
    file_path: Path


def get_artwork_rules(artwork_type: str) -> dict:
    rules = ARTWORK_RULES.get(artwork_type)

    if rules is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid artwork type. "
                "Allowed values: poster, banner, thumbnail."
            ),
        )

    return rules


def validate_aspect_ratio(
    width: int,
    height: int,
    expected_ratio: float,
) -> bool:
    actual_ratio = width / height

    # Small tolerance prevents problems caused by decimal rounding.
    tolerance = 0.01

    return abs(actual_ratio - expected_ratio) <= tolerance


async def validate_and_save_artwork(
    file: UploadFile,
    artwork_type: str,
    storage_directory: Path,
) -> ValidatedArtwork:
    rules = get_artwork_rules(artwork_type)

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported image type. "
                "Only JPEG, PNG, and WebP images are allowed."
            ),
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    file_size_bytes = len(file_bytes)

    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Artwork file size must not exceed 200 KB.",
        )

    try:
        from io import BytesIO

        image = Image.open(BytesIO(file_bytes))
        image.verify()

        image = Image.open(BytesIO(file_bytes))
        width, height = image.size

    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid image.",
        ) from None

    if width != rules["target_width"] or height != rules["target_height"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"{artwork_type} must be exactly "
                f"{rules['target_width']}x{rules['target_height']} pixels. "
                f"Received {width}x{height}."
            ),
        )

    if not validate_aspect_ratio(
        width,
        height,
        rules["ratio"],
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{artwork_type} has an invalid aspect ratio.",
        )

    storage_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    extension = ".jpg"

    if file.content_type == "image/png":
        extension = ".png"
    elif file.content_type == "image/webp":
        extension = ".webp"

    storage_filename = f"{uuid4().hex}{extension}"
    storage_path = storage_directory / storage_filename

    storage_path.write_bytes(file_bytes)

    return ValidatedArtwork(
        original_filename=Path(file.filename).name,
        storage_key=f"artworks/{storage_filename}",
        mime_type=file.content_type,
        width=width,
        height=height,
        file_size_bytes=file_size_bytes,
        file_path=storage_path,
    )