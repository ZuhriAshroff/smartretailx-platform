from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Product
from app.schemas import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_product_by_sku(db: Session, sku: str) -> Product | None:
    return db.execute(select(Product).where(Product.sku == sku)).scalar_one_or_none()


def search_products(
    db: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    category: str | None = None,
) -> tuple[list[Product], int]:
    stmt = select(Product).where(Product.is_active.is_(True))

    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.description.ilike(like)))
    if category:
        stmt = stmt.where(Product.category == category)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    items = (
        db.execute(stmt.order_by(Product.id).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )
    return items, total


def create_product(db: Session, payload: ProductCreate) -> Product:
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product: Product, payload: ProductUpdate) -> Product:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


def deactivate_product(db: Session, product: Product) -> Product:
    product.is_active = False
    db.commit()
    db.refresh(product)
    return product
