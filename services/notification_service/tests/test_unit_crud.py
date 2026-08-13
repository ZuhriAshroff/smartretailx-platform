from app import crud


def test_create_notification_persists_a_record(db_session):
    notification = crud.create_notification(
        db_session, event_type="order.created", subject="Order received", message="msg", recipient_user_id=1
    )
    assert notification.id is not None
    assert notification.is_read is False


def test_get_notification_returns_none_when_missing(db_session):
    assert crud.get_notification(db_session, 12345) is None


def test_list_notifications_filters_by_recipient(db_session):
    crud.create_notification(db_session, "order.created", "s1", "m1", recipient_user_id=1)
    crud.create_notification(db_session, "order.created", "s2", "m2", recipient_user_id=2)

    items, total = crud.list_notifications(db_session, page=1, page_size=10, recipient_user_id=1)
    assert total == 1
    assert items[0].recipient_user_id == 1


def test_list_notifications_without_filter_returns_all(db_session):
    crud.create_notification(db_session, "order.created", "s1", "m1", recipient_user_id=1)
    crud.create_notification(db_session, "order.created", "s2", "m2", recipient_user_id=2)

    items, total = crud.list_notifications(db_session, page=1, page_size=10)
    assert total == 2


def test_mark_as_read_flips_the_flag(db_session):
    notification = crud.create_notification(db_session, "order.created", "s1", "m1", recipient_user_id=1)
    updated = crud.mark_as_read(db_session, notification)
    assert updated.is_read is True
