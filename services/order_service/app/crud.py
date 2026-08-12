from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem


def create_order(db: Session, customer_id: int, items: list[dict]) -> Order:
    """`items` is a list of {product_id, product_name, quantity, unit_price}."""
    total = sum(item["quantity"] * item["unit_price"] for item in items)
    order = Order(customer_id=customer_id, status="pending", total_amount=total)
    order.items = [OrderItem(**item) for item in items]
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def list_orders(
    db: Session,
    page: int,
    page_size: int,
    customer_id: int | None = None,
    status_filter: str | None = None,
) -> tuple[list[Order], int]:
    stmt = select(Order)
    if customer_id is not None:
        stmt = stmt.where(Order.customer_id == customer_id)
    if status_filter is not None:
        stmt = stmt.where(Order.status == status_filter)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = (
        db.execute(stmt.order_by(Order.id.desc()).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return items, total


def update_order_status(db: Session, order: Order, new_status: str) -> Order:
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
