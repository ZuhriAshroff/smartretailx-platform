def test_list_products_requires_authentication(client):
    response = client.get("/v1/products")
    assert response.status_code == 401


def test_admin_can_create_a_product(client, admin_token):
    response = client.post(
        "/v1/products",
        json={"sku": "SKU-100", "name": "Coffee Beans", "category": "Groceries", "price": 12.5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["sku"] == "SKU-100"


def test_customer_cannot_create_a_product(client, customer_token):
    response = client.post(
        "/v1/products",
        json={"sku": "SKU-101", "name": "Tea Bags", "category": "Groceries", "price": 5.0},
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403


def test_search_and_pagination_return_created_products(client, admin_token, customer_token):
    for i in range(3):
        client.post(
            "/v1/products",
            json={"sku": f"SKU-20{i}", "name": f"Product {i}", "category": "Electronics", "price": 20.0},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    response = client.get(
        "/v1/products?category=Electronics&page=1&page_size=2",
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


def test_admin_can_update_and_soft_delete_a_product(client, admin_token):
    create_response = client.post(
        "/v1/products",
        json={"sku": "SKU-300", "name": "Notebook", "category": "Stationery", "price": 3.5},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    product_id = create_response.json()["id"]

    update_response = client.put(
        f"/v1/products/{product_id}",
        json={"price": 4.0},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["price"] == 4.0

    delete_response = client.delete(
        f"/v1/products/{product_id}", headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert delete_response.status_code == 204
