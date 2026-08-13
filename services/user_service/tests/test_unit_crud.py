from app import crud


def test_create_user_persists_a_hashed_password(db_session):
    user = crud.create_user(db_session, "carol@smartretailx.com", "password123", "Carol Customer")
    assert user.id is not None
    assert user.hashed_password != "password123"
    assert user.role == "customer"


def test_get_user_by_email_returns_none_when_not_found(db_session):
    assert crud.get_user_by_email(db_session, "missing@smartretailx.com") is None


def test_get_user_by_email_finds_an_existing_user(db_session):
    crud.create_user(db_session, "dave@smartretailx.com", "password123", "Dave Staff", role="warehouse_staff")
    found = crud.get_user_by_email(db_session, "dave@smartretailx.com")
    assert found is not None
    assert found.role == "warehouse_staff"


def test_list_users_paginates_results(db_session):
    for i in range(5):
        crud.create_user(db_session, f"user{i}@smartretailx.com", "password123", f"User {i}")

    page_1, total = crud.list_users(db_session, page=1, page_size=2)
    assert total == 5
    assert len(page_1) == 2


def test_update_user_role_changes_the_role(db_session):
    user = crud.create_user(db_session, "erin@smartretailx.com", "password123", "Erin Customer")
    updated = crud.update_user_role(db_session, user, "admin")
    assert updated.role == "admin"


def test_delete_user_removes_the_record(db_session):
    user = crud.create_user(db_session, "frank@smartretailx.com", "password123", "Frank Customer")
    crud.delete_user(db_session, user)
    assert crud.get_user_by_id(db_session, user.id) is None
