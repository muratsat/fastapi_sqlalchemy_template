from fastapi import APIRouter

from app.articles.router import router as articles_router

router = APIRouter()

router.include_router(articles_router, prefix="/articles", tags=["Articles"])
