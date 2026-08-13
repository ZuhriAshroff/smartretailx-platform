def test_list_inventory_requires_staff_or_admin_role(client, customer_token):
    response = client.get("/v1/inventory", headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code == 403


def test_warehouse_staff_can_create_an_inventory_record(client, staff_token):
    response = client.post(
        "/v1/inventory",
        json={"product_id": 10, "sku": "SKU-10", "quantity_available": 100, "reorder_level": 5},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 201
    assert response.json()["quantity_available"] == 100


def test_any_authenticated_user_can_view_a_single_product_stock(client, staff_token, customer_token):
    client.post(
        "/v1/inventory",
        json={"product_id": 11, "sku": "SKU-11", "quantity_available": 30},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    response = client.get("/v1/inventory/11", headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code == 200
    assert response.json()["quantity_available"] == 30


def test_staff_can_restock_via_patch(client, staff_token):
    client.post(
        "/v1/inventory",
        json={"product_id": 12, "sku": "SKU-12", "quantity_available": 5, "reorder_level": 3},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    response = client.patch(
        "/v1/inventory/12",
        json={"quantity_delta": 20},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert response.status_code == 200
    assert response.json()["quantity_available"] == 25
