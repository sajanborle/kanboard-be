from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from jose import jwt

security = HTTPBearer()
SECRET_KEY = "secret"

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except:
        raise HTTPException(status_code=401, detail="Invalid token")