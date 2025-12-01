from __future__ import annotations

from typing import Any

import json
import os
import uuid
import requests


BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8001")


def _print_response(prefix: str, response: requests.Response) -> Any:
    """Pretty-print the response body and return parsed data if possible."""

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            data: Any = response.json()
        except Exception:  # noqa: BLE001
            data = response.text
    else:
        data = response.text

    print(f"{prefix} status={response.status_code}")
    print("Response body:")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(str(data))

    return data


def check(path: str, expected_status: int = 200, **kwargs: Any) -> Any:
    """Helper to perform a GET request and assert basic expectations.

    Luôn in ra response để dễ debug; assert chỉ dùng để phát hiện bất thường.
    """

    url = BASE_URL + path
    response = requests.get(url, **kwargs)
    data = _print_response(f"GET {path}", response)

    assert (
        response.status_code == expected_status
    ), f"Unexpected status for {path}: {response.status_code}"

    return data


def request_json(method: str, path: str, expected_status: int = 200, **kwargs: Any) -> Any:
    """Generic helper for non-GET methods used in tests.

    Luôn in ra response để dễ debug; assert chỉ dùng để phát hiện bất thường.
    """

    url = BASE_URL + path
    response = requests.request(method, url, **kwargs)
    data = _print_response(f"{method} {path}", response)

    assert (
        response.status_code == expected_status
    ), f"Unexpected status for {method} {path}: {response.status_code}"

    return data


def test_auth_flow() -> dict[str, str]:
    """Test auth register/login and return auth headers for subsequent calls.

    This uses the /api/auth/register endpoint to create a fresh user so that
    it is compatible with the current password hashing logic.
    """

    email = f"test_auth_{uuid.uuid4().hex[:8]}@example.com"
    password = "test_password_123"

    # Register new user
    register_resp = request_json(
        "POST",
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert isinstance(register_resp, dict)
    assert register_resp.get("message") == "User registered successfully"

    # Duplicate register should fail with 400
    dup_resp = request_json(
        "POST",
        "/api/auth/register",
        expected_status=400,
        json={"email": email, "password": password},
    )
    assert dup_resp.get("detail") == "Email already registered"

    # Successful login
    login_resp = request_json(
        "POST",
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert isinstance(login_resp, dict)
    assert "access_token" in login_resp
    access_token = login_resp["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Failed login with wrong password
    err_login = request_json(
        "POST",
        "/api/auth/login",
        expected_status=400,
        json={"email": email, "password": "wrong_password"},
    )
    assert err_login.get("detail") == "Incorrect email or password"

    return headers


def test_users_crud() -> None:
    users = check("/api/users")
    assert isinstance(users, list)

    email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    new_user = request_json(
        "POST",
        "/api/users",
        json={
            "email": email,
            "password": "dummy_password",
            "full_name": "Test User",
        },
    )
    assert isinstance(new_user, dict)
    assert new_user["email"] == email
    user_id = new_user["id"]

    fetched = check(f"/api/users/{user_id}")
    assert fetched["id"] == user_id

    updated = request_json(
        "PATCH",
        f"/api/users/{user_id}",
        json={"full_name": "Updated Test User", "is_active": False},
    )
    assert updated["full_name"] == "Updated Test User"
    assert updated["is_active"] is False

    dup_error = request_json(
        "POST",
        "/api/users",
        expected_status=400,
        json={
            "email": email,
            "password": "another_password",
        },
    )
    assert dup_error.get("detail") == "Email already registered"

    _ = request_json("GET", "/api/users/999999", expected_status=404)


def test_menu_crud(first_category_id: int) -> int:
    created = request_json(
        "POST",
        "/api/menu",
        json={
            "category_id": first_category_id,
            "name": "Test Item",
            "price": 12345,
            "description": "Test item created by script",
            "is_available": True,
        },
    )
    assert isinstance(created, dict)
    item_id = created["id"]

    updated = request_json(
        "PATCH",
        f"/api/menu/{item_id}",
        json={
            "name": "Updated Test Item",
            "price": 23456,
        },
    )
    assert updated["id"] == item_id
    assert updated["name"].startswith("Updated")

    deleted = request_json("DELETE", f"/api/menu/{item_id}")
    assert deleted["id"] == item_id
    assert deleted["is_available"] is False

    search_result = check("/api/menu", params={"q": "Trà"})
    assert isinstance(search_result, list)

    return item_id


def test_orders_flow(first_item_id: int, headers: dict[str, str]) -> None:
    draft = request_json(
        "POST",
        "/api/orders/draft",
        json={
            "address": "Test address",
            "note": "Test order from script",
        },
        headers=headers,
    )
    assert isinstance(draft, dict)
    assert draft.get("status") == "DRAFT"
    order_id = draft["id"]

    order_with_item = request_json(
        "POST",
        f"/api/orders/{order_id}/items",
        json={
            "item_id": first_item_id,
            "quantity": 2,
            "option_ids": [],
        },
        headers=headers,
    )
    assert isinstance(order_with_item, dict)
    assert order_with_item.get("status") == "DRAFT"
    assert order_with_item.get("items")
    first_order_item = order_with_item["items"][0]
    order_item_id = first_order_item["id"]
    assert first_order_item["quantity"] == 2

    order_after_update = request_json(
        "PATCH",
        f"/api/orders/{order_id}/items/{order_item_id}",
        json={"quantity": 3},
        headers=headers,
    )
    assert isinstance(order_after_update, dict)
    assert order_after_update.get("items")
    updated_item = next(i for i in order_after_update["items"] if i["id"] == order_item_id)
    assert updated_item["quantity"] == 3

    order_confirmed = request_json(
        "POST",
        f"/api/orders/{order_id}/confirm",
        headers=headers,
    )
    assert order_confirmed.get("status") == "CONFIRMED"

    order_cancelled = request_json(
        "POST",
        f"/api/orders/{order_id}/cancel",
        headers=headers,
    )
    assert order_cancelled.get("status") == "CANCELLED"


def test_orders_errors_and_history(
    headers: dict[str, str],
    unavailable_item_id: int,
    first_item_id: int,
) -> None:
    draft_unavail = request_json(
        "POST",
        "/api/orders/draft",
        json={
            "address": "Error test address",
            "note": "Order with unavailable item",
        },
        headers=headers,
    )
    order_unavail_id = draft_unavail["id"]

    err_unavail = request_json(
        "POST",
        f"/api/orders/{order_unavail_id}/items",
        expected_status=400,
        json={
            "item_id": unavailable_item_id,
            "quantity": 1,
            "option_ids": [],
        },
        headers=headers,
    )
    assert err_unavail.get("detail") == "Menu item is not available"

    empty_draft = request_json(
        "POST",
        "/api/orders/draft",
        json={
            "address": "Empty order",
            "note": "Should fail confirm",
        },
        headers=headers,
    )
    empty_order_id = empty_draft["id"]

    err_confirm = request_json(
        "POST",
        f"/api/orders/{empty_order_id}/confirm",
        expected_status=400,
        headers=headers,
    )
    assert err_confirm.get("detail") == "Cannot confirm an order with no items"

    draft2 = request_json(
        "POST",
        "/api/orders/draft",
        json={
            "address": "Error test 2",
            "note": "Order to test status rules",
        },
        headers=headers,
    )
    order2_id = draft2["id"]

    order2_with_item = request_json(
        "POST",
        f"/api/orders/{order2_id}/items",
        json={
            "item_id": first_item_id,
            "quantity": 1,
            "option_ids": [],
        },
        headers=headers,
    )
    order2_item_id = order2_with_item["items"][0]["id"]

    order2_confirmed = request_json(
        "POST",
        f"/api/orders/{order2_id}/confirm",
        headers=headers,
    )
    assert order2_confirmed.get("status") == "CONFIRMED"

    err_modify_confirmed = request_json(
        "PATCH",
        f"/api/orders/{order2_id}/items/{order2_item_id}",
        expected_status=400,
        json={"quantity": 5},
        headers=headers,
    )
    assert err_modify_confirmed.get("detail") == "Only draft orders can be modified"

    cancelled = request_json(
        "POST",
        f"/api/orders/{order2_id}/cancel",
        headers=headers,
    )
    assert cancelled.get("status") == "CANCELLED"

    err_cancel_again = request_json(
        "POST",
        f"/api/orders/{order2_id}/cancel",
        expected_status=400,
        headers=headers,
    )
    assert err_cancel_again.get("detail") == "Order is already cancelled"

    history_1 = check("/api/orders/history", params={"limit": 1}, headers=headers)
    assert isinstance(history_1, list)
    assert len(history_1) <= 1

    history_10 = check("/api/orders/history", params={"limit": 10}, headers=headers)
    assert isinstance(history_10, list)
    assert len(history_10) >= 1


def run_smoke_tests() -> None:
    """Run a small set of smoke tests against the running API service."""

    # 1. Health check
    health = check("/health")
    assert isinstance(health, dict) and health.get("status") == "ok"

    # 2. Categories
    categories = check("/api/categories")
    assert isinstance(categories, list) and len(categories) >= 1
    first_category_id = categories[0]["id"]

    # 3. Full menu
    menu = check("/api/menu")
    assert isinstance(menu, list) and len(menu) >= 1
    first_item_id = menu[0]["id"]

    # 4. Menu filtered by category
    menu_by_category = check("/api/menu", params={"category_id": first_category_id})
    assert isinstance(menu_by_category, list)

    # 5. Item detail
    item = check(f"/api/menu/{first_item_id}")
    assert isinstance(item, dict) and item["id"] == first_item_id

    # 6. FAQs
    faqs = check("/api/faqs")
    assert isinstance(faqs, list) and len(faqs) >= 1

    faqs_search = check("/api/faqs", params={"q": "mở cửa"})
    assert isinstance(faqs_search, list)

    print("Testing Users CRUD...")
    test_users_crud()

    print("Testing Menu CRUD + search by keyword...")
    unavailable_item_id = test_menu_crud(first_category_id)

    print("Testing Auth (register/login)...")
    headers = test_auth_flow()

    print("Testing Orders flow...")
    test_orders_flow(first_item_id, headers=headers)

    print("Testing Orders error cases + history...")
    test_orders_errors_and_history(headers=headers, unavailable_item_id=unavailable_item_id, first_item_id=first_item_id)

    print("All smoke tests (including extended flows) passed.")


def run_menu_tests() -> None:
    """Run only menu-related tests (categories, menu list/detail, CRUD)."""

    # Health check
    health = check("/health")
    assert isinstance(health, dict) and health.get("status") == "ok"

    # Categories & first category
    categories = check("/api/categories")
    assert isinstance(categories, list) and len(categories) >= 1
    first_category_id = categories[0]["id"]

    # Full menu and first item detail
    menu = check("/api/menu")
    assert isinstance(menu, list) and len(menu) >= 1
    first_item_id = menu[0]["id"]

    menu_by_category = check("/api/menu", params={"category_id": first_category_id})
    assert isinstance(menu_by_category, list)

    item = check(f"/api/menu/{first_item_id}")
    assert isinstance(item, dict) and item["id"] == first_item_id

    print("Testing Menu CRUD + search by keyword...")
    _ = test_menu_crud(first_category_id)

    print("Menu API tests completed.")


if __name__ == "__main__":
    # Chỉ test các API của menu khi chạy trực tiếp file này
    run_menu_tests()