from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.hashing import hash_password, verify_password
from app.utils.token import create_access_token
from app.utils.response import success_response, error_response
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(tags=["Users"])

@router.post("/signup")
async def signup(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(
            select(models.User).where(models.User.email == user.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            return error_response("User already exists", status_code=400)

        new_user = models.User(
            username=user.username,
            email=user.email,
            password=hash_password(user.password),
            role=user.role
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return success_response(
            data={
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "role": new_user.role
            },
            message="User created successfully"
        )

    except Exception as e:
        await db.rollback()
        return error_response(str(e), status_code=500)
            
@router.post("/login")
async def login(user: schemas.UserLogin, db: AsyncSession = Depends(get_db)):

    result = await db.execute(
        select(models.User).where(models.User.email == user.email)
    )
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.password):
        return error_response("Invalid credentials", status_code=401)

    token = create_access_token({
        "sub": db_user.email,
        "role": db_user.role
    })

    return success_response(
        data={
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email,
                "role": db_user.role
            }
        },
        message="Login successful"
    )