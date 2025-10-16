from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, models

from .schemas import User, UserCreate

router = APIRouter()


@router.post("/", response_model=User)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = models.User(name=user.name, phone_number=user.phone_number)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.get("/", response_model=list[User])
async def get_users(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/{id}", response_model=User)
async def get_user(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/{id}", response_model=User)
async def update_user(id: int, user: UserCreate, db: AsyncSession = Depends(get_db)):
    query = (
        update(models.User)
        .where(models.User.id == id)
        .values(name=user.name, phone_number=user.phone_number)
        .returning(models.User)
    )
    result = await db.execute(query)
    db_user = result.scalar_one_or_none()

    await db.commit()
    await db.refresh(db_user)

    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


@router.delete("/{id}")
async def delete_user(id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.id == id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
