"""Exercises the RabbitMQ event handlers directly (without a live broker) to
prove the inventory reservation and auto-provisioning logic that the
background consumer thread invokes on real messages.
"""
from app import consumers, crud


def test_product_created_event_auto_provisions_inventory(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    consumers._handle_product_created({"product_id": 50, "sku": "SKU-50"})
    record = crud.get_by_product_id(db_session, 50)
    assert record is not None
    assert record.quantity_available == 0


def test_order_created_event_reserves_stock_when_available(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    reserved_events = []
    monkeypatch.setattr(
        "app.consumers.publish_inventory_reserved",
        lambda order_id, items: reserved_events.append((order_id, items)),
    )
    crud.create_inventory(db_session, product_id=51, sku="SKU-51", quantity_available=10)

    consumers._handle_order_created({"order_id": 1, "items": [{"product_id": 51, "quantity": 3}]})

    record = crud.get_by_product_id(db_session, 51)
    assert record.quantity_available == 7
    assert record.quantity_reserved == 3
    assert reserved_events == [(1, [{"product_id": 51, "quantity": 3}])]


def test_order_created_event_publishes_insufficient_when_stock_too_low(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    insufficient_events = []
    monkeypatch.setattr(
        "app.consumers.publish_inventory_insufficient",
        lambda order_id, items, reason: insufficient_events.append((order_id, items, reason)),
    )
    crud.create_inventory(db_session, product_id=52, sku="SKU-52", quantity_available=1)

    consumers._handle_order_created({"order_id": 2, "items": [{"product_id": 52, "quantity": 5}]})

    record = crud.get_by_product_id(db_session, 52)
    assert record.quantity_available == 1  # untouched, nothing reserved
    assert len(insufficient_events) == 1
    assert insufficient_events[0][0] == 2
