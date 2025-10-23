import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import rate_limiter
from app.auth import create_token_pair, get_user, rotate_refresh_token
from app.auth.schemas import (
    OneTimeCodeInput,
    RefreshTokenSchema,
    TokenPair,
    VerifyCodeInput,
)
from app.db import get_db, models

router = APIRouter()

logger = logging.getLogger(__name__)

OTP_LENGTH = 6
MAX_OTP_ATTEMPTS = 5


async def send_otp(phone_number: str, code: str):
    # TODO: Send OTP to user
    print(phone_number, code)
    pass


def random_otp() -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(OTP_LENGTH)])


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()


@router.post("/request-otp")
async def request_otp(
    request: Request, otp_input: OneTimeCodeInput, db: AsyncSession = Depends(get_db)
):
    await rate_limiter.rate_limit(request, max_requests=5, timeframe_seconds=10)
    otp = random_otp()

    db_code = await db.execute(
        insert(models.OneTimeCode)
        .values(
            phone_number=otp_input.phone_number,
            code=hash_otp(otp),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            attempts=0,
            used=False,
        )
        .on_conflict_do_update(
            index_elements=["phone_number"],
            set_=dict(
                code=hash_otp(otp),
                attempts=0,
                used=False,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            ),
        )
        .returning(models.OneTimeCode)
    )
    db_code = db_code.scalar_one()

    try:
        await send_otp(otp_input.phone_number, otp)
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to send OTP to {otp_input.phone_number}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not send one time code",
        )

    await db.commit()


@router.post("/token")
async def verify_otp(
    request, otp_input: VerifyCodeInput, db: AsyncSession = Depends(get_db)
) -> TokenPair:
    await rate_limiter.rate_limit(request, max_requests=5, timeframe_seconds=10)
    db_code = (
        await db.execute(
            select(models.OneTimeCode).where(
                models.OneTimeCode.phone_number == otp_input.phone_number
            )
        )
    ).scalar_one_or_none()

    # Check if code exists and is not expired
    if db_code is None or db_code.expires_at <= datetime.now(timezone.utc):
        logger.warning(
            f"Invalid or expired OTP attempt for phone: {otp_input.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code is invalid"
        )

    # Check if code has already been used
    if db_code.used:
        logger.warning(f"Attempted reuse of OTP for phone: {otp_input.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code is invalid"
        )

    # Check if max attempts exceeded
    if db_code.attempts >= MAX_OTP_ATTEMPTS:
        logger.warning(f"Max OTP attempts exceeded for phone: {otp_input.phone_number}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Please request a new code.",
        )

    # Verify the code
    codes_match = secrets.compare_digest(hash_otp(otp_input.code), db_code.code)

    if not codes_match:
        # Increment attempts on failed verification
        await db.execute(
            update(models.OneTimeCode)
            .where(models.OneTimeCode.phone_number == otp_input.phone_number)
            .values(attempts=db_code.attempts + 1)
        )
        await db.commit()
        logger.warning(
            f"Failed OTP verification attempt {db_code.attempts + 1}/{MAX_OTP_ATTEMPTS} "
            f"for phone: {otp_input.phone_number}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Code is invalid"
        )

    # Mark code as used
    await db.execute(
        update(models.OneTimeCode)
        .where(models.OneTimeCode.phone_number == otp_input.phone_number)
        .values(used=True)
    )

    # Create or update user
    user = (
        await db.execute(
            insert(models.User)
            .values(
                id=str(uuid.uuid4()),
                phone_number=otp_input.phone_number,
                name=otp_input.name,
            )
            .on_conflict_do_update(
                index_elements=["phone_number"],
                set_=dict(phone_number=otp_input.phone_number),
            )
            .returning(models.User)
        )
    ).scalar_one()

    token_pair = await create_token_pair(user.id, db)
    await db.commit()

    logger.info(f"Successful OTP verification for phone: {otp_input.phone_number}")
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
