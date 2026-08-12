import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.events import publish_product_created, publish_product_deleted, publish_product_updated
from app.schemas import PaginatedProducts, ProductCreate, ProductPublic, ProductUpdate
from libs.common.security import TokenPayload, get_current_user, require_roles

logger = logging.getLogger("product_service.products")
router = APIRouter(prefix="/v1/products", tags=["products"])


@router.get("", response_model=PaginatedProducts)
def search_products(
    q: str | None = Query(default=None, description="Free-text search across name/description"),
    category: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total = crud.search_products(db, page, page_size, q=q, category=category)
    return PaginatedProducts(total=total, page=page, page_size=page_size, items=items)


@router.get("/{product_id}", response_model=ProductPublic)
def get_product(
    product_id: int,
    _current_user: TokenPayload = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("", response_model=ProductPublic, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    _admin: TokenPayload = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if crud.get_product_by_sku(db, payload.sku):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SKU already exists")

    product = crud.create_product(db, payload)

    try:
        publish_product_created(product.id, product.sku, product.name, product.category, float(product.price))
    except Exception:
        logger.exception("Failed to publish product.created event for product %s", product.id)

    return product


@router.put("/{product_id}", response_model=ProductPublic)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    _admin: TokenPayload = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    updated = crud.update_product(db, product, payload)

    try:
        publish_product_updated(updated.id, updated.sku, payload.model_dump(exclude_unset=True))
    except Exception:
        logger.exception("Failed to publish product.updated event for product %s", updated.id)

    return updated


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    _admin: TokenPayload = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    crud.deactivate_product(db, product)

    try:
        publish_product_deleted(product.id, product.sku)
    except Exception:
        logger.exception("Failed to publish product.deleted event for product %s", product.id)
