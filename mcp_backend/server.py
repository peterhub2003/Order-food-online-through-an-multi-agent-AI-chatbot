from __future__ import annotations

from typing import Any, Dict, List, Optional

import os

import httpx
from mcp.server.fastmcp import FastMCP


BACKEND_API_BASE_URL = os.getenv("BACKEND_API_BASE_URL", "http://backend:8000")
MCP_BACKEND_PORT = int(os.getenv("MCP_BACKEND_PORT", "8000"))


mcp = FastMCP("backend-tools", host="0.0.0.0", port=MCP_BACKEND_PORT)


async def _backend_request(
    method: str,
    path: str,
    *,
    access_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
    timeout_seconds: float = 10.0,
) -> Dict[str, Any]:

    url = BACKEND_API_BASE_URL.rstrip("/") + path
    timeout = httpx.Timeout(timeout_seconds)

    headers: Dict[str, str] = {"accept": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
            )
        except httpx.HTTPError as exc:  
            return {
                "ok": False,
                "status_code": None,
                "error": str(exc),
                "data": None,
            }

    try:
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data: Any = response.json()
        else:
            data = response.text
    except Exception as exc: 
        data = None
        parse_error = str(exc)
    else:
        parse_error = None

    ok = response.status_code >= 200 and response.status_code < 300

    return {
        "ok": ok,
        "status_code": response.status_code,
        "error": None if ok else response.text,
        "parse_error": parse_error,
        "data": data,
    }





@mcp.tool()
async def backend_health() -> Dict[str, Any]:
    """Check health of the food-ordering backend service."""

    return await _backend_request("GET", "/health")


@mcp.tool()
async def list_categories() -> Dict[str, Any]:
    """List all menu categories from the backend.

    Wraps GET /api/categories.
    """

    return await _backend_request("GET", "/api/categories")


@mcp.tool()
async def list_menu(
    category_id: Optional[int] = None,
    q: Optional[str] = None,
) -> Dict[str, Any]:
    """List available menu items, optionally filtered.

    Args:
        category_id: Optional category id to filter by.
        q: Optional keyword to search in item name.

    Wraps GET /api/menu.
    """

    params: Dict[str, Any] = {}
    if category_id is not None:
        params["category_id"] = category_id
    if q:
        params["q"] = q

    return await _backend_request("GET", "/api/menu", params=params)


@mcp.tool()
async def get_menu_item(item_id: int) -> Dict[str, Any]:
    """Get details of a single menu item by id.

    Wraps GET /api/menu/{item_id}.
    """

    return await _backend_request("GET", f"/api/menu/{item_id}")


@mcp.tool()
async def list_faqs(q: Optional[str] = None) -> Dict[str, Any]:
    """List FAQs, optionally filtered by a search keyword.

    Wraps GET /api/faqs.
    """

    params: Dict[str, Any] = {}
    if q:
        params["q"] = q

    return await _backend_request("GET", "/api/faqs", params=params)





@mcp.tool()
async def get_order_history(
    limit: int = 10,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Get recent orders for the currently authenticated user.

    Wraps GET /api/orders/history with the given JWT access token.
    """

    params = {"limit": limit}
    return await _backend_request(
        "GET",
        "/api/orders/history",
        access_token=access_token,
        params=params,
    )


@mcp.tool()
async def create_draft_order(
    access_token: Optional[str] = None,
    address: Optional[str] = None,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new draft order for the authenticated user.

    Wraps POST /api/orders/draft.
    """

    payload: Dict[str, Any] = {}
    if address is not None:
        payload["address"] = address
    if note is not None:
        payload["note"] = note

    return await _backend_request(
        "POST",
        "/api/orders/draft",
        access_token=access_token,
        json=payload,
    )


@mcp.tool()
async def get_order(
    order_id: int,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Get details of a specific order for the authenticated user.

    Wraps GET /api/orders/{order_id}.
    """

    return await _backend_request(
        "GET",
        f"/api/orders/{order_id}",
        access_token=access_token,
    )


    @mcp.tool()
    async def add_item_to_order(
        order_id: int,
        item_id: int,
        quantity: int = 1,
        option_ids: Optional[List[int]] = None,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add an item (and optional options) to a draft order.

        Wraps POST /api/orders/{order_id}/items.
        """

        if option_ids is None:
            option_ids = []

        payload = {
            "item_id": item_id,
            "quantity": quantity,
            "option_ids": option_ids,
        }

        return await _backend_request(
            "POST",
            f"/api/orders/{order_id}/items",
            access_token=access_token,
            json=payload,
        )


@mcp.tool()
async def update_order_item(
    order_id: int,
    order_item_id: int,
    quantity: Optional[int] = None,
    option_ids: Optional[List[int]] = None,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Update quantity and/or options for an item in a draft order.

    Wraps PATCH /api/orders/{order_id}/items/{order_item_id}.
    """

    payload: Dict[str, Any] = {}
    if quantity is not None:
        payload["quantity"] = quantity
    if option_ids is not None:
        payload["option_ids"] = option_ids

    return await _backend_request(
        "PATCH",
        f"/api/orders/{order_id}/items/{order_item_id}",
        access_token=access_token,
        json=payload,
    )


@mcp.tool()
async def remove_order_item(
    order_id: int,
    order_item_id: int,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Remove an item from a draft order.

    Wraps DELETE /api/orders/{order_id}/items/{order_item_id}.
    """

    return await _backend_request(
        "DELETE",
        f"/api/orders/{order_id}/items/{order_item_id}",
        access_token=access_token,
    )


@mcp.tool()
async def confirm_order(
    order_id: int,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Confirm a draft order for the authenticated user.

    Wraps POST /api/orders/{order_id}/confirm.
    """

    return await _backend_request(
        "POST",
        f"/api/orders/{order_id}/confirm",
        access_token=access_token,
    )


@mcp.tool()
async def cancel_order(
    order_id: int,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel an order for the authenticated user if allowed by status.

    Wraps POST /api/orders/{order_id}/cancel.
    """

    return await _backend_request(
        "POST",
        f"/api/orders/{order_id}/cancel",
        access_token=access_token,
    )


@mcp.tool()
async def calculate_bill(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate the total bill amount accurately.
    
    Use this tool whenever you need to calculate the total price for a list of items 
    to avoid arithmetic errors.

    Args:
        items: A list of dictionaries. Each dictionary must have:
               - 'price' (int/float): The unit price of the item.
               - 'quantity' (int): The number of items (default to 1 if missing).
               Example: [{"price": 50000, "quantity": 2}, {"price": 35000, "quantity": 1}]
    
    Returns:
        Dict containing the total amount and a breakdown string.
    """
    total = 0.0
    breakdown_parts = []
    
    for item in items:
        price = float(item.get("price", 0))
        quantity = int(item.get("quantity", 1))
        subtotal = price * quantity
        total += subtotal
        if price > 0:
            breakdown_parts.append(f"{price:,.0f}x{quantity}")
    
    return {
        "total_amount": total,
        "formatted_total": f"{total:,.0f} VND",
        "breakdown": " + ".join(breakdown_parts) + f" = {total:,.0f}"
    }

@mcp.tool()
async def estimate_delivery_fee(
    order_id: int,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    """Estimate delivery fee for an order."""

    return {
        "ok": True,
        "status_code": 200,
        "error": None,
        "parse_error": None,
        "data": {"delivery_fee": 10000},
    }


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
