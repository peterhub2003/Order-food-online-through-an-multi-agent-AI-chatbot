from __future__ import annotations

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    items: Mapped[list["MenuItem"]] = relationship("MenuItem", back_populates="category")


class MenuItem(Base):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Store price as decimal; for simplicity we rely on Numeric here.
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    category: Mapped["Category"] = relationship("Category", back_populates="items")
    option_groups: Mapped[list["ItemOptionGroup"]] = relationship(
        "ItemOptionGroup", back_populates="item", cascade="all, delete-orphan"
    )


class ItemOptionGroup(Base):
    __tablename__ = "item_option_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("menu_items.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    multi_select: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="option_groups")
    options: Mapped[list["ItemOption"]] = relationship(
        "ItemOption", back_populates="group", cascade="all, delete-orphan"
    )


class ItemOption(Base):
    __tablename__ = "item_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("item_option_groups.id"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    extra_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    group: Mapped["ItemOptionGroup"] = relationship("ItemOptionGroup", back_populates="options")
