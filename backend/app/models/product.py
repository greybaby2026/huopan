"""产品与产品图片模型"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ProductStatus(str, PyEnum):
    """产品状态枚举"""
    DRAFT = "draft"        # 草稿
    ACTIVE = "active"      # 上架
    ARCHIVED = "archived"  # 归档


class Product(Base):
    """产品主表"""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="款号")
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="产品名称")
    category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, comment="品类: 衬衫/卫衣/夹克/裤装等")
    color: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="颜色")
    pattern: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="花型: 纯色/条纹/格纹/印花")
    season: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="季节: 春/夏/秋/冬")
    style: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="风格: 商务/休闲/运动")
    fabric: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="面料")

    size_range: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="尺码范围, 逗号分隔: S,M,L,XL")
    cost_price: Mapped[float] = mapped_column(Float, default=0, comment="成本价")
    supply_price: Mapped[float] = mapped_column(Float, default=0, comment="供应价")
    retail_price: Mapped[float] = mapped_column(Float, default=0, comment="零售价(备用)")
    stock: Mapped[int] = mapped_column(Integer, default=0, comment="库存数量")

    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus), default=ProductStatus.DRAFT, index=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order"
    )
    catalogs: Mapped[list["Catalog"]] = relationship(back_populates="product")

    def __repr__(self):
        return f"<Product {self.sku_code}>"


class ProductImage(Base):
    """产品图片"""
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    original_path: Mapped[str] = mapped_column(String(512), comment="原图路径(相对 uploads 目录)")
    thumbnail_path: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="缩略图路径")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序, 0为主图")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped[Product] = relationship(back_populates="images")

    def __repr__(self):
        return f"<ProductImage product_id={self.product_id} order={self.sort_order}>"
