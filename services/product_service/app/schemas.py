from datetime import datetime

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    category: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    currency: str = Field(default="GBP", min_length=3, max_length=3)


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    price: float | None = Field(default=None, gt=0)
    currency: str | None = None
    is_active: bool | None = None


class ProductPublic(BaseModel):
    id: int
    sku: str
    name: str
    description: str
    category: str
    price: float
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedProducts(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductPublic]
