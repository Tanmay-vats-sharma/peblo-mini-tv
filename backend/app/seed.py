import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Artwork, Episode, Season, Show


BASE_DIR = Path(__file__).resolve().parent.parent
SEED_FILE = BASE_DIR / "seed_shows.json"


def load_seed_data() -> list[dict]:
    with SEED_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("seed_shows.json must contain a list of records")

    return data


def get_or_create_show(db: Session, record: dict) -> Show:
    slug = record["slug"]

    show = db.scalar(
        select(Show).where(Show.slug == slug)
    )

    if show is None:
        show = Show(
            title=record["show_title"],
            slug=slug,
            description=record.get("synopsis"),
            section=record.get("section"),
            categories=record.get("categories", []),
            is_published=record.get("status") == "published",
        )

        db.add(show)
        db.flush()

    return show


def get_or_create_season(
    db: Session,
    show: Show,
    record: dict,
) -> Season:
    season_number = record["season_number"]

    season = db.scalar(
        select(Season).where(
            Season.show_id == show.id,
            Season.season_number == season_number,
        )
    )

    if season is None:
        season = Season(
            show_id=show.id,
            season_number=season_number,
            title=(
                "Trailers"
                if season_number == 0
                else f"Season {season_number}"
            ),
            description=record.get("synopsis"),
        )

        db.add(season)
        db.flush()

    return season


def episode_already_exists(
    db: Session,
    record: dict,
) -> bool:
    existing_episode = db.scalar(
        select(Episode).where(
            Episode.seed_episode_id == record["episode_id"],
        )
    )

    return existing_episode is not None

def create_episode(
    db: Session,
    season: Season,
    record: dict,
) -> Episode | None:
    if episode_already_exists(db, record):
        return None

    episode = Episode(
        seed_episode_id=record["episode_id"],
        season_id=season.id,
        title=record["episode_title"],
        episode_number=record["episode_number"],
        content_group=record["content_group"],
        language=record["language"],
        status=record.get("status", "draft"),
        description=record.get("synopsis"),
        duration_seconds=record.get("duration_seconds"),
    )

    db.add(episode)
    db.flush()

    return episode


def create_artworks(
    db: Session,
    show: Show,
    record: dict,
) -> int:
    artwork_items = record.get("artwork_available", [])

    if not artwork_items:
        return 0

    created_count = 0

    for artwork_type in artwork_items:
        image_url = (
            f"/artwork/{record['slug']}/"
            f"{artwork_type}.jpg"
        )

        existing_artwork = db.scalar(
            select(Artwork).where(
                Artwork.show_id == show.id,
                Artwork.artwork_type == artwork_type,
                Artwork.image_url == image_url,
            )
        )

        if existing_artwork is not None:
            continue

        artwork = Artwork(
            show_id=show.id,
            artwork_type=artwork_type,
            image_url=image_url,
        )

        db.add(artwork)
        created_count += 1

    return created_count


def seed_database() -> None:
    records = load_seed_data()

    db = SessionLocal()

    created_shows = 0
    created_seasons = 0
    created_episodes = 0
    created_artworks = 0

    try:
        for record in records:
            show_before = db.scalar(
                select(Show).where(Show.slug == record["slug"])
            )

            show = get_or_create_show(db, record)

            if show_before is None:
                created_shows += 1

            season_before = db.scalar(
                select(Season).where(
                    Season.show_id == show.id,
                    Season.season_number == record["season_number"],
                )
            )

            season = get_or_create_season(db, show, record)

            if season_before is None:
                created_seasons += 1

            episode = create_episode(db, season, record)

            if episode is not None:
                created_episodes += 1

            created_artworks += create_artworks(
                db,
                show,
                record,
            )

        db.commit()

        print("Seed completed successfully")
        print(f"Shows created: {created_shows}")
        print(f"Seasons created: {created_seasons}")
        print(f"Episodes created: {created_episodes}")
        print(f"Artwork records created: {created_artworks}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()