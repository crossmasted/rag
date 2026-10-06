from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.db import get_db
from app.models.visit import Visit

router = APIRouter()


@router.get("")
async def get_visits(db: Session = Depends(get_db)):
    """返回当前访问量（不加）"""
    row = db.query(Visit).first()
    return {"count": row.count if row else 0}


@router.post("")
async def increment_visits(db: Session = Depends(get_db)):
    """访问量 +1，返回最新值"""
    row = db.query(Visit).first()
    if row is None:
        row = Visit()
        row.count = 1
        db.add(row)
    else:
        row.count += 1
    db.commit()
    db.refresh(row)
    return {"count": row.count}