from datetime import datetime, timedelta, timezone
import random

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import OneTimeCodeInput, Token, VerifyCodeInput
from app.db import get_db, models
from app.config import env

router = APIRouter()

ALGORITHM = "HS256"
SECRET_KEY = env.SECRET_KEY


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/request-code")
async def request_code(otp_input: OneTimeCodeInput, db: AsyncSession = Depends(get_db)):
    random_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
    db_code = (
        await db.execute(
            select(models.OneTimeCode).where(
                models.OneTimeCode.phone_number == otp_input.phone_number
            )
        )
    ).scalar_one_or_none()

    if db_code is None:
        db_code = (
            await db.execute(
                insert(models.OneTimeCode)
                .values(phone_number=otp_input.phone_number, code=random_code)
                .returning(models.OneTimeCode)
            )
        ).scalar_one()
        db.add(db_code)

    db_code.code = random_code

    await db.commit()
    await db.refresh(db_code)


@router.post("/verify-code")
async def verify_code(otp_input: VerifyCodeInput, db: AsyncSession = Depends(get_db)):
    db_code = (
        await db.execute(
            select(models.OneTimeCode).where(
                models.OneTimeCode.phone_number == otp_input.phone_number
            )
        )
    ).scalar_one_or_none()

    if db_code is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code is invalid"
        )

    verified = db_code.code == otp_input.code

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code is invalid"
        )

    user = await db.execute(
        select(models.User).where(models.User.phone_number == otp_input.phone_number)
    )
    user = user.scalar_one_or_none()
    if user is None:
        user = models.User(phone_number=otp_input.phone_number, name=otp_input.name)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=timedelta(minutes=15)
    )

    return Token(access_token=access_token, token_type="bearer")


async def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id = int(payload.get("sub"))

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await db.execute(select(models.User).where(models.User.id == user_id))
    user = user.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


@router.get("/me")
async def get_current_user(current_user: models.User = Depends(get_user)):
    return current_user
