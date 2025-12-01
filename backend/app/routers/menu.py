from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.menu import Category, MenuItem
from ..schemas.menu import CategoryOut, MenuItemCreateIn, MenuItemOut, MenuItemUpdateIn


router = APIRouter(tags=["menu"])


@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(db: Session = Depends(get_db)) -> List[CategoryOut]:  # noqa: B008
    categories = db.query(Category).order_by(Category.name).all()
    return [CategoryOut.model_validate(cat) for cat in categories]


@router.get("/menu", response_model=List[MenuItemOut])
async def list_menu(
    category_id: int | None = Query(default=None),
    q: str | None = Query(default=None, description="Search keyword in item name"),
    db: Session = Depends(get_db),  
) -> List[MenuItemOut]:
    query = db.query(MenuItem).filter(MenuItem.is_available.is_(True))

    if category_id is not None:
        query = query.filter(MenuItem.category_id == category_id)

    if q:
        like = f"%{q}%"
        query = query.filter(MenuItem.name.ilike(like))

    items = query.order_by(MenuItem.name).all()


    result: List[MenuItemOut] = []
    for item in items:
        _ = item.option_groups  
        for group in item.option_groups:
            _ = group.options 
        result.append(MenuItemOut.model_validate(item))

    return result


@router.get("/menu/{item_id}", response_model=MenuItemOut)
async def get_menu_item(item_id: int, db: Session = Depends(get_db)) -> MenuItemOut:  
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    _ = item.option_groups  
    for group in item.option_groups:
        _ = group.options 

    return MenuItemOut.model_validate(item)


@router.post("/menu", response_model=MenuItemOut)
async def create_menu_item(
    payload: MenuItemCreateIn,
    db: Session = Depends(get_db), 
) -> MenuItemOut:
    category = db.query(Category).filter(Category.id == payload.category_id).first()
    if category is None:
        raise HTTPException(status_code=400, detail="Category not found")

    item = MenuItem(
        category_id=payload.category_id,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        is_available=payload.is_available,
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return MenuItemOut.model_validate(item)

@router.patch("/menu/{item_id}", response_model=MenuItemOut)
async def update_menu_item(
    item_id: int,
    payload: MenuItemUpdateIn,
    db: Session = Depends(get_db),  
) -> MenuItemOut:
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if payload.category_id is not None and payload.category_id != item.category_id:
        category = db.query(Category).filter(Category.id == payload.category_id).first()
        if category is None:
            raise HTTPException(status_code=400, detail="Category not found")
        item.category_id = payload.category_id

    if payload.name is not None:
        item.name = payload.name
    if payload.description is not None:
        item.description = payload.description
    if payload.price is not None:
        item.price = payload.price
    if payload.is_available is not None:
        item.is_available = payload.is_available

    db.commit()
    db.refresh(item)

    return MenuItemOut.model_validate(item)


@router.delete("/menu/{item_id}", response_model=MenuItemOut)
async def delete_menu_item(item_id: int, db: Session = Depends(get_db)) -> MenuItemOut: 
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Soft delete: mark as unavailable so existing order references remain valid.
    item.is_available = False
    db.commit()
    db.refresh(item)

    return MenuItemOut.model_validate(item)
