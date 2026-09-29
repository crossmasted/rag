from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    access_level: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=UserOut)
async def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册用户"""
    exists = db.query(User).filter(User.username == req.username).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    user = User(username=req.username, password_hash=hash_password(req.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login")
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    """登录，返回 JWT"""
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer", "user": UserOut.model_validate(user)}
