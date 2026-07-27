"""产品 CRUD + 图片上传 + 批量操作 API"""
from pathlib import Path
import json

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.product import Product, ProductImage, ProductStatus
from app.schemas.product import (
    ProductCreate, ProductUpdate, ProductOut,
    ProductBatchUpdate, ProductListResponse,
)
from app.services.image_service import save_upload_image
from app.services.log_service import log_operation

router = APIRouter(prefix="/products", tags=["产品"])


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: str | None = Query(None, description="搜索款号或名称"),
    category: str | None = None,
    color: str | None = None,
    season: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """产品列表, 支持分页和多条件检索"""
    query = select(Product).options(selectinload(Product.images))

    if keyword:
        query = query.where(
            or_(
                Product.sku_code.ilike(f"%{keyword}%"),
                Product.name.ilike(f"%{keyword}%"),
            )
        )
    if category:
        query = query.where(Product.category == category)
    if color:
        query = query.where(Product.color == color)
    if season:
        query = query.where(Product.season == season)
    if status:
        try:
            query = query.where(Product.status == ProductStatus(status))
        except ValueError:
            raise HTTPException(400, f"无效状态: {status}")

    # 总数
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # 分页
    query = query.offset((page - 1) * page_size).limit(page_size).order_by(Product.id.desc())
    result = await db.execute(query)
    items = result.scalars().unique().all()

    return ProductListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Product).options(selectinload(Product.images)).where(Product.id == product_id)
    product = (await db.execute(query)).scalar_one_or_none()
    if not product:
        raise HTTPException(404, "产品不存在")
    return product


@router.post("", response_model=ProductOut)
async def create_product(
    data: ProductCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 款号唯一检查
    existing = await db.execute(select(Product).where(Product.sku_code == data.sku_code))
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"款号 {data.sku_code} 已存在")

    product = Product(**data.model_dump())
    try:
        product.status = ProductStatus(data.status)
    except ValueError:
        product.status = ProductStatus.DRAFT

    db.add(product)
    await db.commit()
    await db.refresh(product)
    # 重新查询加载 images 关系
    result = await db.execute(
        select(Product).options(selectinload(Product.images)).where(Product.id == product.id)
    )
    product_out = result.scalar_one()

    # 操作日志
    await log_operation(
        db, action="create", resource_type="product",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        resource_id=product.id,
        detail=f"创建产品: {data.sku_code} {data.name}",
    )
    await db.commit()

    return product_out


@router.put("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int, data: ProductUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "产品不存在")

    update_data = data.model_dump(exclude_unset=True)

    # 款号唯一检查
    if "sku_code" in update_data and update_data["sku_code"] != product.sku_code:
        existing = await db.execute(
            select(Product).where(Product.sku_code == update_data["sku_code"])
        )
        if existing.scalar_one_or_none():
            raise HTTPException(409, f"款号 {update_data['sku_code']} 已存在")

    if "status" in update_data:
        try:
            product.status = ProductStatus(update_data["status"])
        except ValueError:
            raise HTTPException(400, f"无效状态: {update_data['status']}")
        del update_data["status"]

    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()

    # 操作日志
    await log_operation(
        db, action="update", resource_type="product",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        resource_id=product.id,
        detail=f"更新产品: {product.sku_code}",
    )
    await db.commit()

    # 重新查询加载 images 关系
    result = await db.execute(
        select(Product).options(selectinload(Product.images)).where(Product.id == product.id)
    )
    return result.scalar_one()


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "产品不存在")
    await db.delete(product)
    await db.commit()

    # 操作日志
    await log_operation(
        db, action="delete", resource_type="product",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        resource_id=product_id,
        detail=f"删除产品: {product.sku_code} {product.name}",
    )
    await db.commit()

    return {"message": "已删除"}


@router.post("/{product_id}/images", response_model=ProductOut)
async def upload_product_images(
    product_id: int,
    files: list[UploadFile] = File(...),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为产品上传图片, 支持批量"""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "产品不存在")

    # 查现有图片数, 决定起始 sort_order
    existing_count = await db.execute(
        select(func.count()).select_from(ProductImage).where(ProductImage.product_id == product_id)
    )
    sort_start = existing_count.scalar() or 0

    for idx, file in enumerate(files):
        file_bytes = await file.read()
        if len(file_bytes) > settings.max_image_size_mb * 1024 * 1024:
            raise HTTPException(413, f"图片 {file.filename} 超过 {settings.max_image_size_mb}MB 限制")

        original_rel, thumb_rel = save_upload_image(file_bytes, file.filename or "upload.jpg")
        img = ProductImage(
            product_id=product_id,
            original_path=original_rel,
            thumbnail_path=thumb_rel,
            sort_order=sort_start + idx,
        )
        db.add(img)

    await db.commit()
    await db.refresh(product)
    # 重新加载 images 关系
    await db.refresh(product, attribute_names=["images"])
    return product


@router.delete("/{product_id}/images/{image_id}")
async def delete_product_image(
    product_id: int, image_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    img = await db.get(ProductImage, image_id)
    if not img or img.product_id != product_id:
        raise HTTPException(404, "图片不存在")

    # 删除文件
    for rel_path in (img.original_path, img.thumbnail_path):
        if rel_path:
            full_path = Path(settings.upload_dir) / rel_path
            if full_path.exists():
                full_path.unlink()

    await db.delete(img)
    await db.commit()
    return {"message": "图片已删除"}


@router.post("/batch", response_model=dict)
async def batch_update_products(
    data: ProductBatchUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量更新产品"""
    update_data = data.updates.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, "没有需要更新的字段")

    # status 特殊处理
    status_value = None
    if "status" in update_data:
        try:
            status_value = ProductStatus(update_data.pop("status"))
        except ValueError:
            raise HTTPException(400, f"无效状态: {data.updates.status}")

    result = await db.execute(
        select(Product).where(Product.id.in_(data.ids))
    )
    products = result.scalars().all()
    if not products:
        raise HTTPException(404, "未找到指定产品")

    for product in products:
        for key, value in update_data.items():
            setattr(product, key, value)
        if status_value:
            product.status = status_value

    await db.commit()

    # 操作日志 (批量)
    await log_operation(
        db, action="batch_update", resource_type="product",
        user_id=user.get("user_id") if user else None,
        username=user.get("username") if user else None,
        detail=f"批量更新 {len(products)} 个产品",
    )
    await db.commit()

    return {"message": f"已更新 {len(products)} 个产品", "updated_count": len(products)}


@router.get("/meta/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """获取所有品类(用于筛选下拉)"""
    result = await db.execute(
        select(Product.category).distinct().where(Product.category.isnot(None))
    )
    return {"categories": [r[0] for r in result.all() if r[0]]}


@router.get("/import/template")
async def download_import_template():
    """下载产品导入 Excel 模板"""
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from urllib.parse import quote
    from app.services.import_service import generate_import_template

    excel_bytes = generate_import_template()
    filename = quote("产品导入模板.xlsx")

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"},
    )


@router.post("/import")
async def import_products(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """批量导入产品: 上传 Excel, 解析并导入. 已存在的款号跳过."""
    from app.services.import_service import parse_import_excel
    from app.models.product import ProductStatus

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(400, "文件为空")

    try:
        products_data = parse_import_excel(file_bytes)
    except Exception as e:
        raise HTTPException(400, f"Excel 解析失败: {str(e)}")

    if not products_data:
        raise HTTPException(400, "未找到有效数据行")

    created = 0
    skipped = 0
    errors = []

    for idx, pdata in enumerate(products_data, 2):  # 行号从2开始(跳过表头)
        # 款号唯一检查
        existing = await db.execute(
            select(Product).where(Product.sku_code == pdata["sku_code"])
        )
        if existing.scalar_one_or_none():
            skipped += 1
            errors.append(f"第{idx}行: 款号 {pdata['sku_code']} 已存在, 跳过")
            continue

        try:
            product = Product(
                sku_code=pdata["sku_code"],
                name=pdata["name"],
                category=pdata.get("category"),
                color=pdata.get("color"),
                pattern=pdata.get("pattern"),
                season=pdata.get("season"),
                style=pdata.get("style"),
                fabric=pdata.get("fabric"),
                size_range=pdata.get("size_range"),
                cost_price=pdata.get("cost_price", 0),
                retail_price=pdata.get("retail_price", 0),
                stock=pdata.get("stock", 0),
                status=ProductStatus(pdata.get("status", "draft")),
                note=pdata.get("note"),
            )
            db.add(product)
            created += 1
        except Exception as e:
            errors.append(f"第{idx}行: {str(e)}")
            skipped += 1

    await db.commit()

    return {
        "message": f"导入完成: 新增 {created} 个, 跳过 {skipped} 个",
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }
