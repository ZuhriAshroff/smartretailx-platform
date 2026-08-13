def test_list_notifications_requires_authentication(client):
    response = client.get("/v1/notifications")
    assert response.status_code == 401


def test_customer_only_sees_their_own_notifications(client, db_session, customer_token):
    from app import crud

    crud.create_notification(db_session, "order.created", "s1", "m1", recipient_user_id=1)
    crud.create_notification(db_session, "order.created", "s2", "m2", recipient_user_id=2)

    response = client.get("/v1/notifications", headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["recipient_user_id"] == 1


def test_admin_sees_all_notifications(client, db_session, admin_token):
    from app import crud

    crud.create_notification(db_session, "order.created", "s1", "m1", recipient_user_id=1)
    crud.create_notification(db_session, "order.created", "s2", "m2", recipient_user_id=2)

    response = client.get("/v1/notifications", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_customer_cannot_read_another_customers_notification(client, db_session, customer_token, other_customer_token):
    from app import crud

    # customer_token belongs to user_id=1; this notification belongs to user_id=1 too,
    # so requesting it as other_customer_token (user_id=2) must be forbidden.
    notification = crud.create_notification(db_session, "order.created", "s1", "m1", recipient_user_id=1)

    response = client.get(
        f"/v1/notifications/{notification.id}", headers={"Authorization": f"Bearer {other_customer_token}"}
    )
    assert response.status_code == 403


def test_owner_can_mark_their_notification_as_read(client, db_session, customer_token):
    from app import crud

    notification = crud.create_notification(db_session, "order.created", "s1", "m1", recipient_user_id=1)

    response = client.patch(
        f"/v1/notifications/{notification.id}/read", headers={"Authorization": f"Bearer {customer_token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_read"] is True
