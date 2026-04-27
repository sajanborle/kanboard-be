from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.utils.deps import get_current_user
from app.utils.response import success_response

router = APIRouter(tags=["Users"])

@router.get("/")
def get_users(db: Session = Depends(get_db),current_user = Depends(get_current_user)):

    users = db.query(
        models.User.id,
        models.User.username,
        models.User.email,
        models.User.role
    ).all()

    result = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role
        }
        for u in users
    ]
    return success_response(data=users, message="Users fetched successfully")