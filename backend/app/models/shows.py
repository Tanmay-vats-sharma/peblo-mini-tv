from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShowSection(str, PyEnum):
    FEATURED = "featured"
    SERIES = "series"
    MINISODES = "minisodes"
    SONGS = "songs"


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    section: Mapped[ShowSection] = mapped_column(
        Enum(ShowSection, name="show_section"),
        nullable=False,
        index=True,
    )

    release_year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    seasons = relationship(
        "Season",
        back_populates="show",
        cascade="all, delete-orphan",
        order_by="Season.season_number",
    )

    artworks = relationship(
        "Artwork",
        back_populates="show",
        cascade="all, delete-orphan",
    )