"""产品相关 Pydantic schema"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ProductImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_path: str
    thumbnail_path: str | None = None
    sort_order: int = 0


class ProductBase(BaseModel):
    sku_code: str = Field(..., max_length=64, description="货号")
    name: str = Field(..., max_length=128)
    category: str | None = None
    color: str | None = None
    pattern: str | None = None
    season: str | None = None
    style: str | None = None
    fabric: str | None = None
    size_range: str | None = None
    cost_price: float = Field(default=0, ge=0)
    supply_price: float = Field(default=0, ge=0, description="供应价")
    retail_price: float = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    status: str = "draft"
    note: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku_code: str | None = None
    name: str | None = None
    category: str | None = None
    color: str | None = None
    pattern: str | None = None
    season: str | None = None
    style: str | None = None
    fabric: str | None = None
    size_range: str | None = None
    cost_price: float | None = Field(default=None, ge=0)
    supply_price: float | None = Field(default=None, ge=0, description="供应价")
    retail_price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    status: str | None = None
    note: str | None = None


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    images: list[ProductImageOut] = []


class ProductBatchUpdate(BaseModel):
    """批量更新"""
    ids: list[int]
    updates: ProductUpdate


class ProductListResponse(BaseModel):
    """分页列表响应"""
    total: int
    page: int
    page_size: int
    items: list[ProductOut]
