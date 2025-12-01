from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class OrderItemOptionOut(BaseModel):
    id: int
    order_item_id: int
    option_id: int
    extra_price: float

    model_config = ConfigDict(from_attributes=True)


class OrderItemOut(BaseModel):
    id: int
    item_id: int
    quantity: int
    unit_price: float
    total_price: float
    options: List[OrderItemOptionOut] = []

    model_config = ConfigDict(from_attributes=True)


class OrderOut(BaseModel):
    id: int
    user_id: int
    status: str
    address: str | None = None
    note: str | None = None
    items: List[OrderItemOut] = []

    model_config = ConfigDict(from_attributes=True)


class OrderCreateDraftIn(BaseModel):
    address: str | None = None
    note: str | None = None


class OrderAddItemIn(BaseModel):
    item_id: int
    quantity: int = 1
    option_ids: List[int] = []


class OrderUpdateItemIn(BaseModel):
    quantity: int | None = None
    option_ids: List[int] | None = None
