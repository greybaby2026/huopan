"""客户与客户分级 API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.customer import Customer, CustomerLevel
from app.schemas.customer import (
    CustomerLevelCreate, CustomerLevelOut,
    CustomerCreate, CustomerUpdate, CustomerOut,
)
from app.services.log_service import log_operation

router = APIRouter(prefix="/customers", tags=["客户"])


# ---- 客户分级 ----

@router.get("/levels", response_model=list[CustomerLevelOut])
async def list_levels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CustomerLevel).order_by(CustomerLevel.sort_order))
    return result.scalars().all()


@router.post("/levels", response_model=CustomerLevelOut)
async def create_level(data: CustomerLevelCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(CustomerLevel).where(CustomerLevel.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"级别 {data.name} 已存在")
    level = CustomerLevel(**data.model_dump())
    db.add(level)
    await db.commit()
    await db.refresh(level)
    return level


@router.put("/levels/{level_id}", response_model=CustomerLevelOut)
async def update_level(level_id: int, data: CustomerLevelCreate, db: AsyncSession = Depends(get_db)):
    level = await db.get(CustomerLevel, level_id)
    if not level:
        raise HTTPException(404, "级别不存在")
    for key, value in data.model_dump().items():
        setattr(level, key, value)
    await db.commit()
    await db.refresh(level)
    return level


@router.delete("/levels/{level_id}")
async def delete_level(level_id: int, db: AsyncSession = Depends(get_db)):
    level = await db.get(CustomerLevel, level_id)
    if not level:
        raise HTTPException(404, "级别不存在")
    await db.delete(level)
    await db.commit()
    return {"message": "已删除"}


# ---- 客户 ----

@router.get("", response_model=list[CustomerOut])
async def list_customers(
    keyword: str | None = Query(None),
    level_id: int | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Customer)
    if keyword:
        query = query.where(
            (Customer.name.ilike(f"%{keyword}%"))
            | (Customer.company.ilike(f"%{keyword}%"))
            | (Customer.contact.ilike(f"%{keyword}%"))
        )
    if level_id is not None:
        query = query.where(Customer.level_id == level_id)
    if is_active is not None:
        query = query.where(Customer.is_active == is_active)
    query = query.order_by(Customer.id.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=CustomerOut)
async def create_customer(
    data: CustomerCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer = Customer(**data.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    await log_operation(db, action="create", resource_type="customer",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        resource_id=customer.id, detail=f"创建客户: {customer.name}")
    await db.commit()

    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: int, data: CustomerUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer = await db.get(Customer, customer_id)
    if not customer: raise HTTPException(404, "客户不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(customer, key, value)
    await db.commit()

    await log_operation(db, action="update", resource_type="customer",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        resource_id=customer.id, detail=f"更新客户: {customer.name}")
    await db.commit()

    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    customer = await db.get(Customer, customer_id)
    if not customer: raise HTTPException(404, "客户不存在")
    name = customer.name
    await db.delete(customer)
    await db.commit()

    await log_operation(db, action="delete", resource_type="customer",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        resource_id=customer_id, detail=f"删除客户: {name}")
    await db.commit()

    return {"message": "已删除"}
