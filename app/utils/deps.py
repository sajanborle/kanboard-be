from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app import models
from jose import jwt
import os

from app.utils.response import error_response 

security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "secret")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    try:
        token = credentials.credentials

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")

        if not email:
            return error_response("Invalid token", status_code=401)

        result = await db.execute(
            select(models.User).where(models.User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return error_response("User not found", status_code=401)

        return user

    except Exception as e:
        print("ERROR:", e)
        return error_response("Invalid token", status_code=401)