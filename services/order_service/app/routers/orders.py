import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.events import publish_order_created, publish_order_status_changed
from app.models import ALLOWED_MANUAL_TRANSITIONS
from app.product_client import ProductNotFoundError, get_product
from app.schemas import OrderCreate, OrderPublic, OrderStatusUpdate, PaginatedOrders
from libs.common.security import TokenPayload, get_current_user, require_roles

logger = logging.getLogger("order_service.orders")
router = APIRouter(prefix="/v1/orders", tags=["orders"])


@router.post("", response_model=OrderPublic, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    request: Request,
    current_user: TokenPayload = Depends(require_roles("customer")),
    db: Session = Depends(get_db),
):
    authorization_header = request.headers.get("authorization", "")
    resolved_items = []
    for item in payload.items:
        try:
            product = get_product(item.product_id, authorization_header)
        except ProductNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item.product_id} does not exist",
            )
        if not product.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {item.product_id} is no longer available",
            )
        resolved_items.append(
            {
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": item.quantity,
                "unit_price": product["price"],
            }
        )

    order = crud.create_order(db, customer_id=int(current_user.sub), items=resolved_items)

    try:
        publish_order_created(order.id, order.customer_id, resolved_items)
    except Exception:
        logger.exception("Failed to publish order.created event for order %s", order.id)

    return order


@router.get("", response_model=PaginatedOrders)
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    customer_filter = None if current_user.role in ("admin", "warehouse_staff") else int(current_user.sub)
    items, total = crud.list_orders(db, page, page_size, customer_id=customer_filter, status_filter=status_filter)
    return PaginatedOrders(total=total, page=page, page_size=page_size, items=items)


@router.get("/{order_id}", response_model=OrderPublic)
def get_order(
    order_id: int,
    current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if current_user.role not in ("admin", "warehouse_staff") and order.customer_id != int(current_user.sub):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not permitted to view this order")
    return order


@router.patch("/{order_id}/status", response_model=OrderPublic)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    _staff: TokenPayload = Depends(require_roles("admin", "warehouse_staff")),
    db: Session = Depends(get_db),
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    allowed_next = ALLOWED_MANUAL_TRANSITIONS.get(order.status, set())
    if payload.status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot transition order from '{order.status}' to '{payload.status}'",
        )

    old_status = order.status
    updated = crud.update_order_status(db, order, payload.status)

    try:
        publish_order_status_changed(updated.id, updated.customer_id, old_status, payload.status)
    except Exception:
        logger.exception("Failed to publish order.status_changed event for order %s", order_id)

    return updated
