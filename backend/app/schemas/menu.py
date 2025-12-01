from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class CategoryOut(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemOptionOut(BaseModel):
    id: int
    name: str
    extra_price: float

    model_config = ConfigDict(from_attributes=True)


class ItemOptionGroupOut(BaseModel):
    id: int
    name: str
    is_required: bool
    multi_select: bool
    options: List[ItemOptionOut]

    model_config = ConfigDict(from_attributes=True)


class MenuItemOut(BaseModel):
    id: int
    category_id: int
    name: str
    description: str | None = None
    price: float
    is_available: bool
    option_groups: List[ItemOptionGroupOut] = []

    model_config = ConfigDict(from_attributes=True)


class MenuItemCreateIn(BaseModel):
    category_id: int
    name: str
    price: float
    description: str | None = None
    is_available: bool = True


class MenuItemUpdateIn(BaseModel):
    category_id: int | None = None
    name: str | None = None
    price: float | None = None
    description: str | None = None
    is_available: bool | None = None
