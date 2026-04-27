from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import SessionLocal
from app.utils.hashing import hash_password, verify_password
from app.utils.token import create_access_token
from app.utils.response import success_response, error_response



router = APIRouter(tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        (models.User.email == user.email) |
        (models.User.username == user.username)
    ).first()

    if existing_user:
        return error_response("User already exists", status_code=400)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )

    db.add(new_user)
    db.commit()

    return success_response(message="User created successfully")

@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    
    db_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not db_user or not verify_password(user.password, db_user.password):
        return error_response("Invalid credentials", status_code=401)

    token = create_access_token({
        "sub": db_user.email,
        "role": db_user.role
    })

    return success_response(
        data={
            "access_token": token,
            "token_type": "bearer"
        },
        message="Login successful"
    )