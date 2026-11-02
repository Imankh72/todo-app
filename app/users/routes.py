from auth.jwt_auth import (
    decode_refresh_token,
    generate_access_token,
    generate_refresh_token,
)
from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from users.models import UserModel
from users.schemas import UserLoginSchema, UserRefreshToken, UserRegisterSchema

DB_SESSION = Depends(get_db)

router = APIRouter(tags=["users"], prefix="/users")


@router.post("/register", status_code=201)
def register(new_user: UserRegisterSchema, db: Session = DB_SESSION):
    if (
        db.query(UserModel)
        .filter(UserModel.username == new_user.username.lower())
        .first()
    ):
        raise HTTPException(status_code=409, detail="username already exists")
    user = UserModel(username=new_user.username.lower())
    user.set_password(new_user.password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "You have registered successfully"}


@router.post("/login", status_code=200)
def login(user: UserLoginSchema, db: Session = DB_SESSION):
    logged_user = (
        db.query(UserModel).filter(UserModel.username == user.username.lower()).first()
    )
    if not logged_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not logged_user.verify_password(user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = generate_access_token(logged_user.id)
    refresh_token = generate_refresh_token(logged_user.id)
    return {
        "detail": "User logged in",
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@router.post("/refresh_token", status_code=200)
def refresh_token(credentials: UserRefreshToken, db: Session = DB_SESSION):
    user_id = decode_refresh_token(credentials.refresh_token)
    access_token = generate_access_token(user_id)
    return {"access_token": access_token}
