from app import crud
from app.models import ALLOWED_MANUAL_TRANSITIONS


def _sample_items():
    return [{"product_id": 1, "product_name": "Widget", "quantity": 2, "unit_price": 5.0}]


def test_create_order_computes_the_total_amount(db_session):
    order = crud.create_order(db_session, customer_id=1, items=_sample_items())
    assert float(order.total_amount) == 10.0
    assert order.status == "pending"
    assert len(order.items) == 1


def test_get_order_returns_none_when_missing(db_session):
    assert crud.get_order(db_session, 9999) is None


def test_list_orders_filters_by_customer_id(db_session):
    crud.create_order(db_session, customer_id=1, items=_sample_items())
    crud.create_order(db_session, customer_id=2, items=_sample_items())

    items, total = crud.list_orders(db_session, page=1, page_size=10, customer_id=1)
    assert total == 1
    assert items[0].customer_id == 1


def test_list_orders_filters_by_status(db_session):
    order = crud.create_order(db_session, customer_id=1, items=_sample_items())
    crud.update_order_status(db_session, order, "confirmed")
    crud.create_order(db_session, customer_id=1, items=_sample_items())

    items, total = crud.list_orders(db_session, page=1, page_size=10, status_filter="confirmed")
    assert total == 1
    assert items[0].status == "confirmed"


def test_update_order_status_changes_state(db_session):
    order = crud.create_order(db_session, customer_id=1, items=_sample_items())
    updated = crud.update_order_status(db_session, order, "confirmed")
    assert updated.status == "confirmed"


def test_allowed_manual_transitions_do_not_permit_skipping_shipped():
    assert "delivered" not in ALLOWED_MANUAL_TRANSITIONS["confirmed"]
    assert "delivered" in ALLOWED_MANUAL_TRANSITIONS["shipped"]
