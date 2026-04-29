from passlib.context import CryptContext
from fastapi import HTTPException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

MAX_PASSWORD_LENGTH = 72

def hash_password(password: str):
    if len(password) > MAX_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail="Password too long (max 72 characters)"
        )
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str):
    if len(plain) > MAX_PASSWORD_LENGTH:
        return False
    return pwd_context.verify(plain, hashed)