from datetime import datetime

from pydantic import BaseModel, Field


class InventoryCreate(BaseModel):
    product_id: int
    sku: str = ""
    quantity_available: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=10, ge=0)


class InventoryAdjust(BaseModel):
    quantity_delta: int = Field(description="Positive to restock, negative to manually deduct stock")
    reorder_level: int | None = Field(default=None, ge=0)


class InventoryPublic(BaseModel):
    id: int
    product_id: int
    sku: str
    quantity_available: int
    quantity_reserved: int
    reorder_level: int
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedInventory(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[InventoryPublic]
