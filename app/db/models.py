from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    phone_number: Mapped[str] = mapped_column(unique=True, index=True)
    name: Mapped[Optional[str]]


class OneTimeCode(Base):
    __tablename__ = "one_time_codes"

    phone_number: Mapped[str] = mapped_column(primary_key=True, index=True, unique=True)
    code: Mapped[str] = mapped_column(primary_key=True, index=True)


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
