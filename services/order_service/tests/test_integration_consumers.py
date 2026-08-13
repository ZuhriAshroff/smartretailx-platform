"""Exercises the RabbitMQ event handlers directly (without a live broker) to
prove that inventory outcomes drive the order status transitions.
"""
from app import consumers, crud


def _sample_items():
    return [{"product_id": 1, "product_name": "Widget", "quantity": 2, "unit_price": 5.0}]


def test_inventory_reserved_event_confirms_a_pending_order(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    status_events = []
    monkeypatch.setattr(
        "app.consumers.publish_order_status_changed",
        lambda order_id, customer_id, old_status, new_status: status_events.append(
            (order_id, old_status, new_status)
        ),
    )
    order = crud.create_order(db_session, customer_id=1, items=_sample_items())

    consumers._handle_inventory_reserved({"order_id": order.id, "items": _sample_items()})

    refreshed = crud.get_order(db_session, order.id)
    assert refreshed.status == "confirmed"
    assert status_events == [(order.id, "pending", "confirmed")]


def test_inventory_insufficient_event_cancels_a_pending_order(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    monkeypatch.setattr("app.consumers.publish_order_status_changed", lambda *a, **k: None)
    order = crud.create_order(db_session, customer_id=1, items=_sample_items())

    consumers._handle_inventory_insufficient(
        {"order_id": order.id, "items": _sample_items(), "reason": "out of stock"}
    )

    refreshed = crud.get_order(db_session, order.id)
    assert refreshed.status == "cancelled"


def test_inventory_reserved_event_is_a_no_op_for_a_non_pending_order(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    events = []
    monkeypatch.setattr(
        "app.consumers.publish_order_status_changed", lambda *a, **k: events.append(a)
    )
    order = crud.create_order(db_session, customer_id=1, items=_sample_items())
    crud.update_order_status(db_session, order, "confirmed")

    consumers._handle_inventory_reserved({"order_id": order.id, "items": _sample_items()})

    assert events == []  # already confirmed, handler should not re-publish
