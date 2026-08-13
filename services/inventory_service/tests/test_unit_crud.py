from app import crud


def test_create_inventory_persists_a_record(db_session):
    record = crud.create_inventory(db_session, product_id=1, sku="SKU-1", quantity_available=50)
    assert record.id is not None
    assert record.quantity_reserved == 0


def test_get_by_product_id_returns_none_when_missing(db_session):
    assert crud.get_by_product_id(db_session, 999) is None


def test_adjust_quantity_increases_stock_on_restock(db_session):
    record = crud.create_inventory(db_session, product_id=2, sku="SKU-2", quantity_available=10)
    updated = crud.adjust_quantity(db_session, record, quantity_delta=5)
    assert updated.quantity_available == 15


def test_adjust_quantity_never_goes_negative(db_session):
    record = crud.create_inventory(db_session, product_id=3, sku="SKU-3", quantity_available=2)
    updated = crud.adjust_quantity(db_session, record, quantity_delta=-10)
    assert updated.quantity_available == 0


def test_try_reserve_stock_succeeds_when_sufficient(db_session):
    crud.create_inventory(db_session, product_id=4, sku="SKU-4", quantity_available=20)
    success = crud.try_reserve_stock(db_session, product_id=4, quantity=5)
    record = crud.get_by_product_id(db_session, 4)
    assert success is True
    assert record.quantity_available == 15
    assert record.quantity_reserved == 5


def test_try_reserve_stock_fails_when_insufficient(db_session):
    crud.create_inventory(db_session, product_id=5, sku="SKU-5", quantity_available=1)
    success = crud.try_reserve_stock(db_session, product_id=5, quantity=5)
    record = crud.get_by_product_id(db_session, 5)
    assert success is False
    assert record.quantity_available == 1


def test_release_reserved_stock_returns_stock_to_available(db_session):
    crud.create_inventory(db_session, product_id=6, sku="SKU-6", quantity_available=10)
    crud.try_reserve_stock(db_session, product_id=6, quantity=4)
    crud.release_reserved_stock(db_session, product_id=6, quantity=4)
    record = crud.get_by_product_id(db_session, 6)
    assert record.quantity_available == 10
    assert record.quantity_reserved == 0
