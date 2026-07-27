"""货盘 API: 生成/查询/改价/批量"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.catalog import Catalog, PriceHistory, StockStatus
from app.models.product import Product
from app.schemas.catalog import CatalogCreate, CatalogUpdate, CatalogOut, CatalogBatchCreate

router = APIRouter(prefix="/catalogs", tags=["货盘"])


@router.get("")
async def list_catalogs(
    customer_id: int | None = None,
    product_id: int | None = None,
    name: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Catalog).options(
        selectinload(Catalog.product).selectinload(Product.images),
        selectinload(Catalog.customer),
    )
    if customer_id is not None:
        query = query.where(Catalog.customer_id == customer_id)
    if product_id is not None:
        query = query.where(Catalog.product_id == product_id)
    if name:
        query = query.where(Catalog.name.ilike(f"%{name}%"))

    query = query.order_by(Catalog.id.desc())
    result = await db.execute(query)
    catalogs = result.scalars().unique().all()

    # 手动序列化, 包含产品信息
    items = []
    for c in catalogs:
        items.append({
            "id": c.id,
            "name": c.name,
            "customer_id": c.customer_id,
            "product_id": c.product_id,
            "price": c.price,
            "min_order_qty": c.min_order_qty,
            "stock_status": c.stock_status.value if c.stock_status else None,
            "note": c.note,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "product": {
                "id": c.product.id,
                "sku_code": c.product.sku_code,
                "name": c.product.name,
                "category": c.product.category,
                "color": c.product.color,
                "size_range": c.product.size_range,
                "supply_price": c.product.supply_price,
                "images": [
                    {"thumbnail_path": img.thumbnail_path, "original_path": img.original_path}
                    for img in c.product.images
                ],
            } if c.product else None,
            "customer": {
                "id": c.customer.id,
                "name": c.customer.name,
            } if c.customer else None,
        })
    return {"items": items, "total": len(items)}


@router.post("", response_model=CatalogOut)
async def create_catalog(
    data: CatalogCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await db.get(Product, data.product_id)
    if not product:
        raise HTTPException(404, "产品不存在")

    catalog = Catalog(**data.model_dump())
    try:
        catalog.stock_status = StockStatus(data.stock_status)
    except ValueError:
        catalog.stock_status = StockStatus.AVAILABLE

    db.add(catalog)
    await db.flush()

    # 记录价格历史
    history = PriceHistory(
        product_id=data.product_id,
        catalog_id=catalog.id,
        new_price=data.price,
        change_type="create",
    )
    db.add(history)
    await db.commit()
    await db.refresh(catalog)
    return catalog


@router.put("/{catalog_id}", response_model=CatalogOut)
async def update_catalog(
    catalog_id: int, data: CatalogUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "货盘项不存在")

    update_data = data.model_dump(exclude_unset=True)
    old_price = catalog.price

    if "stock_status" in update_data:
        try:
            catalog.stock_status = StockStatus(update_data.pop("stock_status"))
        except ValueError:
            raise HTTPException(400, f"无效库存状态: {data.stock_status}")

    for key, value in update_data.items():
        setattr(catalog, key, value)

    # 价格变更记录历史
    if "price" in update_data and update_data["price"] != old_price:
        history = PriceHistory(
            product_id=catalog.product_id,
            catalog_id=catalog.id,
            old_price=old_price,
            new_price=catalog.price,
            change_type="update",
        )
        db.add(history)

    await db.commit()
    await db.refresh(catalog)
    return catalog


@router.delete("/{catalog_id}")
async def delete_catalog(
    catalog_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    catalog = await db.get(Catalog, catalog_id)
    if not catalog:
        raise HTTPException(404, "货盘项不存在")
    await db.delete(catalog)
    await db.commit()
    return {"message": "已删除"}


@router.post("/batch", response_model=dict)
async def batch_create_catalogs(
    data: CatalogBatchCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """按客户级别批量生成货盘: 选产品范围 + 折扣率 -> 自动算价"""
    result = await db.execute(
        select(Product).where(Product.id.in_(data.product_ids))
    )
    products = result.scalars().all()
    if not products:
        raise HTTPException(404, "未找到指定产品")

    created = []
    for product in products:
        price = round(product.supply_price * data.level_discount_rate, 2)
        catalog = Catalog(
            name=data.name,
            customer_id=data.customer_id,
            product_id=product.id,
            price=price,
            min_order_qty=data.min_order_qty,
            stock_status=StockStatus.AVAILABLE,
        )
        db.add(catalog)
        await db.flush()
        created.append(catalog.id)

        history = PriceHistory(
            product_id=product.id,
            catalog_id=catalog.id,
            new_price=price,
            change_type="batch",
        )
        db.add(history)

    await db.commit()
    return {"message": f"已生成 {len(created)} 个货盘项", "created_ids": created, "created_count": len(created)}


@router.get("/price-history/{product_id}")
async def get_price_history(product_id: int, db: AsyncSession = Depends(get_db)):
    """查询产品价格变更历史"""
    result = await db.execute(
        select(PriceHistory)
        .where(PriceHistory.product_id == product_id)
        .order_by(PriceHistory.created_at.desc())
    )
    items = result.scalars().all()
    return {
        "items": [
            {
                "id": h.id,
                "old_price": h.old_price,
                "new_price": h.new_price,
                "change_type": h.change_type,
                "changed_by": h.changed_by,
                "note": h.note,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in items
        ]
    }
