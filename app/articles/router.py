from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, models

from .schemas import Article, ArticleCreate, Status

router = APIRouter()


@router.post("/", response_model=Article)
async def create_article(article: ArticleCreate, db: AsyncSession = Depends(get_db)):
    db_article = models.Article(**article.model_dump())
    db.add(db_article)

    await db.commit()
    await db.refresh(db_article)

    return db_article


@router.get("/", response_model=list[Article])
async def get_articles(
    status: Status, limit=10, offset=0, db: AsyncSession = Depends(get_db)
):
    now = datetime.now()
    print(now)

    if status == "scheduled":
        query = select(models.Article).where(models.Article.scheduled_date > now)
    elif status == "archived":
        query = select(models.Article).where(models.Article.archived_date < now)
    else:
        query = select(models.Article).where(
            and_(
                or_(
                    models.Article.scheduled_date == None,
                    models.Article.scheduled_date < now,
                ),
                or_(
                    models.Article.archived_date == None,
                    models.Article.archived_date > now,
                ),
            )
        )

    result = await db.execute(query.limit(limit).offset(offset))
    articles = result.scalars().all()

    return articles
