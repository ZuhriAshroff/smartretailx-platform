from datetime import datetime

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderItemPublic(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


class OrderPublic(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: float
    items: list[OrderItemPublic]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(shipped|delivered|cancelled)$")


class PaginatedOrders(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[OrderPublic]
