"""货盘与价格历史模型"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class StockStatus(str, PyEnum):
    """库存状态枚举"""
    AVAILABLE = "available"   # 可供货
    LOW_STOCK = "low_stock"   # 紧张
    SOLD_OUT = "sold_out"     # 断货


class Catalog(Base):
    """货盘: 客户(或客户级别) x 产品 的价格映射"""
    __tablename__ = "catalogs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="货盘名称")
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), nullable=True, index=True, comment="指定客户, 为空则按级别"
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    price: Mapped[float] = mapped_column(Float, nullable=False, comment="该货盘专属价格")
    min_order_qty: Mapped[int] = mapped_column(Integer, default=1, comment="起订量")
    stock_status: Mapped[StockStatus] = mapped_column(
        Enum(StockStatus), default=StockStatus.AVAILABLE, comment="供货状态"
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="catalogs")
    customer: Mapped["Customer | None"] = relationship(back_populates="catalogs")

    def __repr__(self):
        return f"<Catalog {self.name} product={self.product_id} price={self.price}>"


class PriceHistory(Base):
    """价格变更记录, 用于追溯"""
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    catalog_id: Mapped[int | None] = mapped_column(ForeignKey("catalogs.id", ondelete="SET NULL"), nullable=True)
    old_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_price: Mapped[float] = mapped_column(Float, nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作人")
    change_type: Mapped[str] = mapped_column(String(32), comment="变更类型: create/update/batch")
    note: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
