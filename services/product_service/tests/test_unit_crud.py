from app import crud
from app.schemas import ProductCreate, ProductUpdate


def _make_product(db_session, sku="SKU-001", category="Groceries"):
    return crud.create_product(
        db_session,
        ProductCreate(sku=sku, name="Test Product", description="desc", category=category, price=9.99),
    )


def test_create_product_persists_expected_fields(db_session):
    product = _make_product(db_session)
    assert product.id is not None
    assert product.is_active is True


def test_get_product_by_sku_finds_existing_product(db_session):
    _make_product(db_session, sku="SKU-002")
    found = crud.get_product_by_sku(db_session, "SKU-002")
    assert found is not None
    assert found.sku == "SKU-002"


def test_search_products_filters_by_category(db_session):
    _make_product(db_session, sku="SKU-A", category="Electronics")
    _make_product(db_session, sku="SKU-B", category="Groceries")

    items, total = crud.search_products(db_session, page=1, page_size=10, category="Electronics")
    assert total == 1
    assert items[0].sku == "SKU-A"


def test_search_products_supports_free_text_query(db_session):
    crud.create_product(
        db_session,
        ProductCreate(sku="SKU-C", name="Wireless Mouse", description="", category="Electronics", price=15.0),
    )
    items, total = crud.search_products(db_session, page=1, page_size=10, q="mouse")
    assert total == 1
    assert items[0].sku == "SKU-C"


def test_update_product_applies_partial_changes(db_session):
    product = _make_product(db_session, sku="SKU-003")
    updated = crud.update_product(db_session, product, ProductUpdate(price=19.99))
    assert float(updated.price) == 19.99
    assert updated.name == "Test Product"


def test_deactivate_product_sets_is_active_false(db_session):
    product = _make_product(db_session, sku="SKU-004")
    deactivated = crud.deactivate_product(db_session, product)
    assert deactivated.is_active is False
