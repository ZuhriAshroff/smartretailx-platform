import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.events import publish_inventory_low_stock, publish_inventory_updated
from app.schemas import InventoryAdjust, InventoryCreate, InventoryPublic, PaginatedInventory
from libs.common.security import TokenPayload, get_current_user, require_roles

logger = logging.getLogger("inventory_service.inventory")
router = APIRouter(prefix="/v1/inventory", tags=["inventory"])


@router.get("", response_model=PaginatedInventory)
def list_inventory(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _staff: TokenPayload = Depends(require_roles("admin", "warehouse_staff")),
    db: Session = Depends(get_db),
):
    items, total = crud.list_inventory(db, page, page_size)
    return PaginatedInventory(total=total, page=page, page_size=page_size, items=items)


@router.get("/{product_id}", response_model=InventoryPublic)
def get_inventory(
    product_id: int,
    _current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = crud.get_by_product_id(db, product_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory record for this product")
    return record


@router.post("", response_model=InventoryPublic, status_code=status.HTTP_201_CREATED)
def create_inventory(
    payload: InventoryCreate,
    _staff: TokenPayload = Depends(require_roles("admin", "warehouse_staff")),
    db: Session = Depends(get_db),
):
    if crud.get_by_product_id(db, payload.product_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inventory record already exists")
    return crud.create_inventory(
        db,
        product_id=payload.product_id,
        sku=payload.sku,
        quantity_available=payload.quantity_available,
        reorder_level=payload.reorder_level,
    )


@router.patch("/{product_id}", response_model=InventoryPublic)
def adjust_inventory(
    product_id: int,
    payload: InventoryAdjust,
    _staff: TokenPayload = Depends(require_roles("admin", "warehouse_staff")),
    db: Session = Depends(get_db),
):
    record = crud.get_by_product_id(db, product_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No inventory record for this product")

    updated = crud.adjust_quantity(db, record, payload.quantity_delta, payload.reorder_level)

    try:
        publish_inventory_updated(updated.product_id, updated.quantity_available)
        if updated.quantity_available <= updated.reorder_level:
            publish_inventory_low_stock(updated.product_id, updated.sku, updated.quantity_available, updated.reorder_level)
    except Exception:
        logger.exception("Failed to publish inventory update event for product %s", product_id)

    return updated
