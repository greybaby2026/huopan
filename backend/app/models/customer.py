"""客户与客户分级模型"""
from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CustomerLevel(Base):
    """客户分级: A/B/C 等, 每级有默认折扣率和起订量"""
    __tablename__ = "customer_levels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, comment="级别名: A/B/C")
    discount_rate: Mapped[float] = mapped_column(Float, default=1.0, comment="折扣率, 1.0=原价, 0.8=8折")
    default_min_qty: Mapped[int] = mapped_column(Integer, default=1, comment="默认起订量")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序")

    customers: Mapped[list["Customer"]] = relationship(back_populates="level")

    def __repr__(self):
        return f"<CustomerLevel {self.name} discount={self.discount_rate}>"


class Customer(Base):
    """客户表"""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True, comment="客户名称")
    company: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="公司名")
    contact: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="联系人")
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="电话")
    address: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="地址")

    level_id: Mapped[int | None] = mapped_column(ForeignKey("customer_levels.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    note: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="备注")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    level: Mapped[CustomerLevel | None] = relationship(back_populates="customers")
    catalogs: Mapped[list["Catalog"]] = relationship(back_populates="customer")

    def __repr__(self):
        return f"<Customer {self.name}>"
