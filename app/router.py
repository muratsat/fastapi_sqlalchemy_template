from fastapi import APIRouter

from app.articles.router import router as articles_router
from app.auth.router import router as auth_router

router = APIRouter()

router.include_router(articles_router, prefix="/articles", tags=["Articles"])
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
