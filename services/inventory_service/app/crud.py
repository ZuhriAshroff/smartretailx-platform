from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Inventory


def get_by_product_id(db: Session, product_id: int) -> Inventory | None:
    return db.execute(select(Inventory).where(Inventory.product_id == product_id)).scalar_one_or_none()


def list_inventory(db: Session, page: int, page_size: int) -> tuple[list[Inventory], int]:
    total = db.execute(select(func.count()).select_from(Inventory)).scalar_one()
    items = (
        db.execute(select(Inventory).order_by(Inventory.id).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return items, total


def create_inventory(
    db: Session, product_id: int, sku: str = "", quantity_available: int = 0, reorder_level: int = 10
) -> Inventory:
    record = Inventory(
        product_id=product_id,
        sku=sku,
        quantity_available=quantity_available,
        reorder_level=reorder_level,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def adjust_quantity(db: Session, record: Inventory, quantity_delta: int, reorder_level: int | None = None) -> Inventory:
    record.quantity_available = max(0, record.quantity_available + quantity_delta)
    if reorder_level is not None:
        record.reorder_level = reorder_level
    db.commit()
    db.refresh(record)
    return record


def try_reserve_stock(db: Session, product_id: int, quantity: int) -> bool:
    """Attempt to reserve `quantity` units for `product_id`. Returns True on success."""
    record = get_by_product_id(db, product_id)
    if record is None or record.quantity_available < quantity:
        return False
    record.quantity_available -= quantity
    record.quantity_reserved += quantity
    db.commit()
    return True


def release_reserved_stock(db: Session, product_id: int, quantity: int) -> None:
    """Return previously reserved stock to available (e.g. an order was cancelled)."""
    record = get_by_product_id(db, product_id)
    if record is None:
        return
    record.quantity_reserved = max(0, record.quantity_reserved - quantity)
    record.quantity_available += quantity
    db.commit()
