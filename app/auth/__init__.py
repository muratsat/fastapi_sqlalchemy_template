import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import TokenPair
from app.config import env
from app.db import get_db, models

ALGORITHM = "HS256"

SECRET_KEY = env.AUTH_SECRET_KEY
REFRESH_SECRET_KEY = env.AUTH_REFRESH_SECRET_KEY

ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRES = timedelta(days=30)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def create_token_pair(
    user_id: str,
    db: AsyncSession,
    parent_jti: str | None = None,
    token_family: str | None = None,
):
    user = await db.execute(select(models.User).where(models.User.id == user_id))
    user = user.scalar_one_or_none()
    if not user:
        raise CREDENTIALS_EXCEPTION

    now = datetime.now(timezone.utc)
    access_payload = {
        "type": "access",
        "sub": user_id,
        "exp": now + ACCESS_TOKEN_EXPIRES,
    }

    token_family = token_family or str(uuid.uuid4())
    jti = str(uuid.uuid4())

    refresh_payload = {
        "type": "refresh",
        "sub": user_id,
        "exp": now + REFRESH_TOKEN_EXPIRES,
        "jti": jti,
        "family": token_family,
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

    db_refresh_token = models.RefreshToken(
        id=jti,
        token_family=token_family,
        user_id=user_id,
        parent_token_id=parent_jti,
        created_at=now,
        expires_at=now + REFRESH_TOKEN_EXPIRES,
    )
    db.add(db_refresh_token)
    await db.commit()

    return TokenPair(access_token=access_token, refresh_token=refresh_token)


async def rotate_refresh_token(refresh_token: str, db: AsyncSession):
    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise CREDENTIALS_EXCEPTION

    user_id = payload.get("sub")
    jti = payload.get("jti")
    token_family = payload.get("family")

    query = await db.execute(
        select(models.RefreshToken).where(models.RefreshToken.id == jti)
    )
    db_token = query.scalar_one_or_none()
    if not db_token or db_token.revoked:
        await db.execute(
            update(models.RefreshToken)
            .where(models.RefreshToken.token_family == token_family)
            .values(revoked=True)
        )
        await db.commit()
        raise CREDENTIALS_EXCEPTION

    await db.execute(
        update(models.RefreshToken)
        .where(models.RefreshToken.id == jti)
        .values(revoked=True)
    )
    await db.commit()

    token_pair = await create_token_pair(
        user_id, db, parent_jti=jti, token_family=token_family
    )

    return token_pair


async def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
):
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")

    except jwt.InvalidTokenError:
        raise CREDENTIALS_EXCEPTION

    user = await db.execute(select(models.User).where(models.User.id == user_id))
    user = user.scalar_one_or_none()

    if user is None:
        raise CREDENTIALS_EXCEPTION

    return user
