from pathlib import Path
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session


from app.database import get_db
from app.routers.artworks import router as artwork_router
from app.routers.auth import router as auth_router
from app.routers.shows import router as show_router
from app.routers.seasons import router as season_router
from app.routers.episodes import router as episode_router
from app.routers.validation import router as validation_router
from app.routers.catalogue import router as catalogue_router
from app.routers.publish_history import router as publish_history_router


BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIRECTORY = BASE_DIR / "storage"
STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Video Content CMS API",
    description="Backend API for the Video Content CMS and Netflix-style Viewer",
    version="1.0.0",
)

app.include_router(artwork_router)
app.include_router(auth_router)
app.include_router(show_router)
app.include_router(season_router)
app.include_router(episode_router)
app.include_router(validation_router)
app.include_router(catalogue_router)
app.include_router(publish_history_router)

app.mount(
    "/storage",
    StaticFiles(directory=STORAGE_DIRECTORY),
    name="storage",
)


@app.get("/")
def root():
    return {
        "message": "Video Content CMS API is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/health/database")
def database_health_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))
    value = result.scalar_one()

    return {
        "status": "healthy",
        "database": "connected",
        "test_result": value,
    }