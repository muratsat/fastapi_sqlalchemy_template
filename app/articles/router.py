from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, models

from .schemas import Article, ArticleCreate, ArticleUpdate, Status

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

    if status == "scheduled":
        query = select(models.Article).where(
            and_(
                models.Article.scheduled_date != None,
                models.Article.scheduled_date > now,
            )
        )
    elif status == "archived":
        query = select(models.Article).where(
            and_(
                models.Article.archived_date != None, models.Article.archived_date < now
            )
        )
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


@router.get("/{id}", response_model=Article)
async def get_article(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Article).where(models.Article.id == id))

    article = result.scalar_one_or_none()

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    return article


@router.patch("/{id}", response_model=Article)
async def update_article(
    id: int, body: ArticleUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Article).where(models.Article.id == id))

    article = result.scalar_one_or_none()

    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    article.archived_date = datetime.now() if body.archive else None

    await db.commit()
    await db.refresh(article)

    return article
