from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Status = Literal["scheduled", "published", "archived"]


class ArticleBase(BaseModel):
    title: str
    content: str

    scheduled_date: datetime | None = None
    archived_date: datetime | None = None


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(BaseModel):
    archive: bool


class Article(ArticleBase):
    id: int

    class Config:
        from_attributes = True
