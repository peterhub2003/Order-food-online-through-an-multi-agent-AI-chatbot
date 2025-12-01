from __future__ import annotations

# Re-export models so that importing backend.app.models is enough to
# register all tables with SQLAlchemy's Base metadata.

from .user import User  # noqa: F401
from .menu import Category, MenuItem, ItemOptionGroup, ItemOption  # noqa: F401
from .order import Order, OrderItem, OrderItemOption  # noqa: F401
from .faq import FAQ  # noqa: F401
