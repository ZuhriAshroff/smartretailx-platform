import pytest
from fastapi import HTTPException

from libs.common.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_a_different_string_than_the_plain_password():
    hashed = hash_password("Sup3rSecret!")
    assert hashed != "Sup3rSecret!"


def test_verify_password_accepts_the_correct_password():
    hashed = hash_password("Sup3rSecret!")
    assert verify_password("Sup3rSecret!", hashed) is True


def test_verify_password_rejects_an_incorrect_password():
    hashed = hash_password("Sup3rSecret!")
    assert verify_password("wrong-password", hashed) is False


def test_create_and_decode_access_token_round_trips_claims():
    token = create_access_token(user_id=42, email="alice@smartretailx.com", role="customer")
    payload = decode_access_token(token)
    assert payload.sub == "42"
    assert payload.email == "alice@smartretailx.com"
    assert payload.role == "customer"


def test_decode_access_token_rejects_a_malformed_token():
    with pytest.raises(HTTPException) as exc_info:
        decode_access_token("not-a-valid-jwt")
    assert exc_info.value.status_code == 401


def test_create_access_token_supports_a_custom_expiry():
    token = create_access_token(user_id=1, email="bob@smartretailx.com", role="admin", expires_minutes=1)
    payload = decode_access_token(token)
    assert payload.role == "admin"
