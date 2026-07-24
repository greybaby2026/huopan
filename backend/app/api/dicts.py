"""品类与尺码库 CRUD API"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.dicts import Category, Size

router = APIRouter(prefix="/dicts", tags=["数据字典"])


# --- 品类 CRUD ---

class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=64)
    sort_order: int = 0


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.sort_order, Category.id))
    items = result.scalars().all()
    return {"items": [{"id": c.id, "name": c.name, "sort_order": c.sort_order} for c in items]}


@router.post("/categories")
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Category).where(Category.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"品类 {data.name} 已存在")
    c = Category(name=data.name, sort_order=data.sort_order)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {"id": c.id, "name": c.name, "sort_order": c.sort_order}


@router.delete("/categories/{category_id}")
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    c = await db.get(Category, category_id)
    if not c:
        raise HTTPException(404, "品类不存在")
    await db.delete(c)
    await db.commit()
    return {"message": "已删除"}


# --- 尺码 CRUD ---

class SizeCreate(BaseModel):
    name: str = Field(..., max_length=32)
    sort_order: int = 0


@router.get("/sizes")
async def list_sizes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Size).order_by(Size.sort_order, Size.id))
    items = result.scalars().all()
    return {"items": [{"id": s.id, "name": s.name, "sort_order": s.sort_order} for s in items]}


@router.post("/sizes")
async def create_size(data: SizeCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Size).where(Size.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"尺码 {data.name} 已存在")
    s = Size(name=data.name, sort_order=data.sort_order)
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return {"id": s.id, "name": s.name, "sort_order": s.sort_order}


@router.delete("/sizes/{size_id}")
async def delete_size(size_id: int, db: AsyncSession = Depends(get_db)):
    s = await db.get(Size, size_id)
    if not s:
        raise HTTPException(404, "尺码不存在")
    await db.delete(s)
    await db.commit()
    return {"message": "已删除"}
