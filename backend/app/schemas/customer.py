"""客户相关 Pydantic schema"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CustomerLevelBase(BaseModel):
    name: str = Field(..., max_length=32)
    discount_rate: float = Field(default=1.0, ge=0, le=1.0, description="折扣率 1.0=原价 0.8=8折")
    default_min_qty: int = Field(default=1, ge=1)
    sort_order: int = 0


class CustomerLevelCreate(CustomerLevelBase):
    pass


class CustomerLevelOut(CustomerLevelBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class CustomerBase(BaseModel):
    name: str = Field(..., max_length=128)
    company: str | None = None
    contact: str | None = None
    phone: str | None = None
    address: str | None = None
    level_id: int | None = None
    is_active: bool = True
    note: str | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = None
    company: str | None = None
    contact: str | None = None
    phone: str | None = None
    address: str | None = None
    level_id: int | None = None
    is_active: bool | None = None
    note: str | None = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
