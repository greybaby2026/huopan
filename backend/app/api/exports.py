"""Excel 导出 API"""
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.catalog import Catalog, StockStatus
from app.models.customer import Customer
from app.models.product import Product
from app.services.excel_service import export_catalog_to_excel
from app.services.log_service import log_operation

router = APIRouter(prefix="/export", tags=["导出"])


@router.get("/catalog/{catalog_name}/excel")
async def export_catalog_excel(
    catalog_name: str,
    customer_id: int | None = None,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导出指定货盘为 Excel, 含图片嵌入"""
    query = select(Catalog).options(
        selectinload(Catalog.product).selectinload(Product.images),
        selectinload(Catalog.customer),
    ).where(Catalog.name == catalog_name)

    if customer_id is not None:
        query = query.where(Catalog.customer_id == customer_id)

    result = await db.execute(query)
    catalogs = result.scalars().unique().all()

    if not catalogs:
        raise HTTPException(404, f"货盘 {catalog_name} 不存在")

    customer_name = None
    if customer_id:
        customer = await db.get(Customer, customer_id)
        customer_name = customer.name if customer else None

    items = []
    for c in catalogs:
        primary_image = None
        if c.product and c.product.images:
            # sort_order=0 为主图
            primary_image = c.product.images[0].original_path

        items.append({
            "sku_code": c.product.sku_code if c.product else "",
            "name": c.product.name if c.product else "",
            "category": c.product.category if c.product else "",
            "color": c.product.color if c.product else "",
            "size_range": c.product.size_range if c.product else "",
            "price": c.price,
            "min_order_qty": c.min_order_qty,
            "stock_status": c.stock_status.value if c.stock_status else "",
            "note": c.note or "",
            "image_path": primary_image,
        })

    excel_bytes = export_catalog_to_excel(catalog_name, items, customer_name)

    # 操作日志
    await log_operation(
        db, action="export", resource_type="catalog",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        resource_id=customer_id,
        detail=f"导出货盘Excel: {catalog_name}",
    )
    await db.commit()

    filename = f"货盘_{catalog_name}"
    if customer_name:
        filename += f"_{customer_name}"
    filename += ".xlsx"

    # URL 编码, 避免 latin-1 编码错误
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@router.get("/catalog/{catalog_name}/images")
async def export_catalog_images(
    catalog_name: str,
    customer_id: int | None = None,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导出货盘所有产品图片为 zip 包"""
    query = select(Catalog).options(
        selectinload(Catalog.product).selectinload(Product.images),
    ).where(Catalog.name == catalog_name)

    if customer_id is not None:
        query = query.where(Catalog.customer_id == customer_id)

    result = await db.execute(query)
    catalogs = result.scalars().unique().all()

    if not catalogs:
        raise HTTPException(404, f"货盘 {catalog_name} 不存在")

    buffer = BytesIO()
    import tempfile
    from app.services.image_service import add_watermark

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for c in catalogs:
            if not c.product:
                continue
            for img in c.product.images:
                full_path = Path(settings.upload_dir) / img.original_path
                if full_path.exists():
                    # 添加水印到临时文件
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        tmp_path = tmp.name
                    try:
                        add_watermark(full_path, tmp_path)
                        # 文件名: 款号_序号.jpg
                        arcname = f"{c.product.sku_code}_{img.sort_order}.jpg"
                        zf.write(tmp_path, arcname)
                    finally:
                        Path(tmp_path).unlink(missing_ok=True)

    buffer.seek(0)
    filename = f"图片包_{catalog_name}.zip"
    from urllib.parse import quote
    encoded_filename = quote(filename)

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )
