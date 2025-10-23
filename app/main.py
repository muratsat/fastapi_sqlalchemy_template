from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.db.redis_cilent import close_redis, init_redis
from app.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup")
    await init_redis()
    yield
    print("Shutdown")
    await close_redis()


app = FastAPI(lifespan=lifespan)


# Global exception handler for SQLAlchemy errors
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(_request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred", "error": str(exc)},
    )


app.include_router(router, prefix="/api")
