from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models.menu import ItemOption, MenuItem
from ..models.order import Order, OrderItem, OrderItemOption
from ..models.user import User
from ..schemas.order import (
    OrderAddItemIn,
    OrderCreateDraftIn,
    OrderOut,
    OrderUpdateItemIn,
)


router = APIRouter(tags=["orders"])


def _get_order_or_404(db: Session, order_id: int, current_user: User | None = None) -> Order:
    query = db.query(Order).filter(Order.id == order_id)
    if current_user is not None:
        query = query.filter(Order.user_id == current_user.id)

    order = query.first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _ensure_draft(order: Order) -> None:
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Only draft orders can be modified")


def _load_order_relations(order: Order) -> None:
    _ = order.items
    for item in order.items:
        _ = item.options


@router.post("/orders/draft", response_model=OrderOut)
async def create_draft_order(
    payload: OrderCreateDraftIn,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = Order(
        user_id=current_user.id,
        status="DRAFT",
        address=payload.address,
        note=payload.note,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    _load_order_relations(order)
    return OrderOut.model_validate(order)


@router.get("/orders/history", response_model=List[OrderOut])
async def get_order_history(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[OrderOut]:
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )

    for order in orders:
        _load_order_relations(order)

    return [OrderOut.model_validate(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = _get_order_or_404(db, order_id, current_user)
    _load_order_relations(order)
    return OrderOut.model_validate(order)


def _recalculate_prices(
    menu_item: MenuItem,
    options: List[ItemOption],
    quantity: int,
) -> tuple[float, float]:
    base_price = float(menu_item.price)
    extra_total = sum(float(opt.extra_price) for opt in options)
    unit_price = base_price + extra_total
    total_price = unit_price * quantity
    return unit_price, total_price


@router.post("/orders/{order_id}/items", response_model=OrderOut)
async def add_item_to_order(
    order_id: int,
    payload: OrderAddItemIn,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = _get_order_or_404(db, order_id, current_user)
    _ensure_draft(order)

    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    menu_item = db.query(MenuItem).filter(MenuItem.id == payload.item_id).first()
    if menu_item is None:
        raise HTTPException(status_code=404, detail="Menu item not found")

    if not menu_item.is_available:
        raise HTTPException(status_code=400, detail="Menu item is not available")

    options: List[ItemOption] = []
    if payload.option_ids:
        options = (
            db.query(ItemOption)
            .filter(ItemOption.id.in_(payload.option_ids))
            .all()
        )
        if len(options) != len(set(payload.option_ids)):
            raise HTTPException(status_code=400, detail="One or more options are invalid")

    unit_price, total_price = _recalculate_prices(menu_item, options, payload.quantity)

    order_item = OrderItem(
        order_id=order.id,
        item_id=menu_item.id,
        quantity=payload.quantity,
        unit_price=unit_price,
        total_price=total_price,
    )
    db.add(order_item)
    db.flush()

    for opt in options:
        db.add(
            OrderItemOption(
                order_item_id=order_item.id,
                option_id=opt.id,
                extra_price=opt.extra_price,
            )
        )

    db.commit()
    db.refresh(order)

    _load_order_relations(order)
    return OrderOut.model_validate(order)


@router.patch("/orders/{order_id}/items/{order_item_id}", response_model=OrderOut)
async def update_order_item(
    order_id: int,
    order_item_id: int,
    payload: OrderUpdateItemIn,
    db: Session = Depends(get_db),  # noqa: B008
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = _get_order_or_404(db, order_id, current_user)
    _ensure_draft(order)

    order_item = (
        db.query(OrderItem)
        .filter(OrderItem.id == order_item_id, OrderItem.order_id == order.id)
        .first()
    )
    if order_item is None:
        raise HTTPException(status_code=404, detail="Order item not found")

    if payload.quantity is not None:
        if payload.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        order_item.quantity = payload.quantity

    options: List[ItemOption] = []
    if payload.option_ids is not None:
        if payload.option_ids:
            options = (
                db.query(ItemOption)
                .filter(ItemOption.id.in_(payload.option_ids))
                .all()
            )
            if len(options) != len(set(payload.option_ids)):
                raise HTTPException(status_code=400, detail="One or more options are invalid")
        db.query(OrderItemOption).filter(
            OrderItemOption.order_item_id == order_item.id
        ).delete(synchronize_session=False)

        for opt in options:
            db.add(
                OrderItemOption(
                    order_item_id=order_item.id,
                    option_id=opt.id,
                    extra_price=opt.extra_price,
                )
            )
    else:
        options = [
            db.query(ItemOption)
            .filter(ItemOption.id == opt.option_id)
            .first()
            for opt in order_item.options
        ]
        options = [opt for opt in options if opt is not None]

    menu_item = db.query(MenuItem).filter(MenuItem.id == order_item.item_id).first()
    if menu_item is None:
        raise HTTPException(status_code=400, detail="Menu item not found for this order item")

    quantity = order_item.quantity
    unit_price, total_price = _recalculate_prices(menu_item, options, quantity)
    order_item.unit_price = unit_price
    order_item.total_price = total_price

    db.commit()
    db.refresh(order)

    _load_order_relations(order)
    return OrderOut.model_validate(order)


@router.delete("/orders/{order_id}/items/{order_item_id}", response_model=OrderOut)
async def delete_order_item(
    order_id: int,
    order_item_id: int,
    db: Session = Depends(get_db),  
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = _get_order_or_404(db, order_id, current_user)
    _ensure_draft(order)

    order_item = (
        db.query(OrderItem)
        .filter(OrderItem.id == order_item_id, OrderItem.order_id == order.id)
        .first()
    )
    if order_item is None:
        raise HTTPException(status_code=404, detail="Order item not found")

    db.delete(order_item)
    db.commit()
    db.refresh(order)

    _load_order_relations(order)
    return OrderOut.model_validate(order)


@router.post("/orders/{order_id}/confirm", response_model=OrderOut)
async def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),  
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = _get_order_or_404(db, order_id, current_user)
    _ensure_draft(order)

    if not order.items:
        raise HTTPException(status_code=400, detail="Cannot confirm an order with no items")

    order.status = "CONFIRMED"
    db.commit()
    db.refresh(order)

    _load_order_relations(order)
    return OrderOut.model_validate(order)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),  
    current_user: User = Depends(get_current_user),
) -> OrderOut:
    order = _get_order_or_404(db, order_id, current_user)

    if order.status == "CANCELLED":
        raise HTTPException(status_code=400, detail="Order is already cancelled")

    order.status = "CANCELLED"
    db.commit()
    db.refresh(order)

    _load_order_relations(order)
    return OrderOut.model_validate(order)
