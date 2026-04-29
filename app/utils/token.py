from jose import jwt
from datetime import datetime, timedelta
import os

from app.utils.timezone import get_ist_time

SECRET_KEY = os.getenv("SECRET_KEY", "secret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    now = get_ist_time() 

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now   
    })

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)