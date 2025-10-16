from fastapi import APIRouter

from app.articles.router import router as articles_router
from app.users.router import router as users_router

router = APIRouter()

router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(articles_router, prefix="/articles", tags=["Articles"])
