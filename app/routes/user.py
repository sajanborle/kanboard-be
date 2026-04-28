from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app import models
from app.utils.deps import get_current_user
from app.utils.response import success_response

router = APIRouter(tags=["Users"])

@router.get("/")
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(
            models.User.id,
            models.User.username,
            models.User.email,
            models.User.role
        )
    )

    users = result.all()

    formatted_users = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]

    return success_response(
        data=formatted_users,
        message="Users fetched successfully"
    )