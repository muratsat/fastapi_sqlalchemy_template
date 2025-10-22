from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(nullable=True)


class OneTimeCode(Base):
    __tablename__ = "one_time_codes"

    phone_number: Mapped[str] = mapped_column(primary_key=True, index=True, unique=True)
    code: Mapped[str] = mapped_column()
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(default=0)
    used: Mapped[bool] = mapped_column(default=False)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(primary_key=True, index=True, unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_family: Mapped[str] = mapped_column(index=True)
    parent_token_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("refresh_tokens.id"), nullable=True
    )
    revoked: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()

    scheduled_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
