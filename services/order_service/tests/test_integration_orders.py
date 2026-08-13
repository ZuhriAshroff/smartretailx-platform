def test_create_order_requires_customer_role(client, staff_token, mock_product):
    response = client.post(
        "/v1/orders",
        json={"items": [{"product_id": 1, "quantity": 1}]},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 403


def test_customer_can_create_an_order(client, customer_token, mock_product):
    response = client.post(
        "/v1/orders",
        json={"items": [{"product_id": 1, "quantity": 2}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["total_amount"] == 20.0


def test_customer_cannot_view_another_customers_order(client, customer_token, other_customer_token, mock_product):
    create_response = client.post(
        "/v1/orders",
        json={"items": [{"product_id": 1, "quantity": 1}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    order_id = create_response.json()["id"]

    response = client.get(f"/v1/orders/{order_id}", headers={"Authorization": f"Bearer {other_customer_token}"})
    assert response.status_code == 403


def test_staff_can_view_any_order_and_list_all(client, customer_token, staff_token, mock_product):
    client.post(
        "/v1/orders",
        json={"items": [{"product_id": 1, "quantity": 1}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    response = client.get("/v1/orders", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_staff_cannot_skip_directly_from_pending_to_shipped(client, customer_token, staff_token, mock_product):
    create_response = client.post(
        "/v1/orders",
        json={"items": [{"product_id": 1, "quantity": 1}]},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    order_id = create_response.json()["id"]

    response = client.patch(
        f"/v1/orders/{order_id}/status",
        json={"status": "shipped"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 409
