def test_get_my_profile_requires_authentication(client):
    response = client.get("/v1/users/me")
    assert response.status_code == 401


def test_get_my_profile_returns_the_authenticated_users_profile(client, admin_token):
    from libs.common.security import create_access_token

    register_response = client.post(
        "/v1/auth/register",
        json={"email": "kate@smartretailx.com", "password": "password123", "full_name": "Kate Customer"},
    )
    user_id = register_response.json()["id"]
    token = create_access_token(user_id=user_id, email="kate@smartretailx.com", role="customer")

    response = client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "kate@smartretailx.com"


def test_non_admin_cannot_create_users_with_arbitrary_roles(client):
    from libs.common.security import create_access_token

    token = create_access_token(user_id=1, email="leo@smartretailx.com", role="customer")
    response = client.post(
        "/v1/users",
        json={"email": "new@smartretailx.com", "password": "password123", "full_name": "New Staff", "role": "admin"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_can_create_a_warehouse_staff_user(client, admin_token):
    response = client.post(
        "/v1/users",
        json={
            "email": "staff@smartretailx.com",
            "password": "password123",
            "full_name": "Staff Member",
            "role": "warehouse_staff",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["role"] == "warehouse_staff"


def test_admin_can_list_all_users_with_pagination(client, admin_token):
    for i in range(3):
        client.post(
            "/v1/auth/register",
            json={"email": f"bulk{i}@smartretailx.com", "password": "password123", "full_name": f"Bulk {i}"},
        )

    response = client.get("/v1/users?page=1&page_size=2", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 3
    assert len(body["items"]) == 2
