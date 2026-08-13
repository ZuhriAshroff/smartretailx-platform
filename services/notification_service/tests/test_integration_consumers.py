"""Exercises the event dispatch table directly (without a live broker) to
prove every published SmartRetailX event is translated into a stored
notification, including the catch-all fallback for unmapped event types.
"""
from app import consumers, crud


def test_user_registered_event_creates_a_welcome_notification(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    consumers._dispatch(
        "user.registered", {"user_id": 5, "email": "new@smartretailx.com", "full_name": "New User", "role": "customer"}
    )
    items, total = crud.list_notifications(db_session, page=1, page_size=10, recipient_user_id=5)
    assert total == 1
    assert "Welcome" in items[0].subject


def test_order_status_changed_event_notifies_the_customer(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    consumers._dispatch(
        "order.status_changed",
        {"order_id": 7, "customer_id": 3, "old_status": "pending", "new_status": "confirmed"},
    )
    items, total = crud.list_notifications(db_session, page=1, page_size=10, recipient_user_id=3)
    assert total == 1
    assert "confirmed" in items[0].message


def test_unmapped_event_type_falls_back_to_generic_system_notification(db_session, monkeypatch):
    monkeypatch.setattr("app.consumers.SessionLocal", lambda: db_session)
    consumers._dispatch("product.created", {"product_id": 9, "sku": "SKU-9"})
    items, total = crud.list_notifications(db_session, page=1, page_size=10)
    assert total == 1
    assert items[0].event_type == "product.created"
