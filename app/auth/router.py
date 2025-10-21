import random
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_token_pair, get_user, rotate_refresh_token
from app.auth.schemas import (
    OneTimeCodeInput,
    RefreshTokenSchema,
    TokenPair,
    VerifyCodeInput,
)
from app.config import env
from app.db import get_db, models

router = APIRouter()


@router.post("/request-otp")
async def request_otp(otp_input: OneTimeCodeInput, db: AsyncSession = Depends(get_db)):
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


@router.post("/token")
async def verify_otp(
    otp_input: VerifyCodeInput, db: AsyncSession = Depends(get_db)
) -> TokenPair:
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
    verified = verified or env.DEBUG

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code is invalid"
        )

    user = await db.execute(
        select(models.User).where(models.User.phone_number == otp_input.phone_number)
    )
    user = user.scalar_one_or_none()
    if user is None:
        user = models.User(
            id=str(uuid.uuid4()),
            phone_number=otp_input.phone_number,
            name=otp_input.name,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token_pair = await create_token_pair(str(user.id), db)

    return token_pair


@router.get("/token/verify")
async def get_current_user(current_user: models.User = Depends(get_user)):
    return current_user


@router.post("/token/refresh")
async def refresh_token(
    refresh_input: RefreshTokenSchema, db: AsyncSession = Depends(get_db)
) -> TokenPair:
    token_pair = await rotate_refresh_token(refresh_input.refresh_token, db)
    return token_pair
