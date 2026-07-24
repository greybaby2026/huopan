"""货盘相关 Pydantic schema"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CatalogBase(BaseModel):
    name: str = Field(..., max_length=128)
    customer_id: int | None = None
    product_id: int
    price: float = Field(..., ge=0)
    min_order_qty: int = Field(default=1, ge=1)
    stock_status: str = "available"
    note: str | None = None


class CatalogCreate(CatalogBase):
    pass


class CatalogUpdate(BaseModel):
    name: str | None = None
    customer_id: int | None = None
    product_id: int | None = None
    price: float | None = Field(default=None, ge=0)
    min_order_qty: int | None = Field(default=None, ge=1)
    stock_status: str | None = None
    note: str | None = None


class CatalogOut(CatalogBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class CatalogBatchCreate(BaseModel):
    """按客户级别批量生成货盘"""
    product_ids: list[int]
    customer_id: int | None = None
    level_discount_rate: float = Field(..., ge=0, le=1.0, description="级别折扣率, 用零售价乘以此值")
    name: str = Field(..., max_length=128)
    min_order_qty: int = Field(default=1, ge=1)
