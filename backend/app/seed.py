from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy.orm import Session

from .db import Base, SessionLocal, engine
from .models import (
    Category,
    FAQ,
    ItemOption,
    ItemOptionGroup,
    MenuItem,
    User,
)


@contextmanager
def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables based on SQLAlchemy models."""
    Base.metadata.create_all(bind=engine)


def seed_users(db: Session) -> None:
    if db.query(User).first():
        return

    users = [
        User(
            email="alice@example.com",
            hashed_password="dummy_hashed_password_alice",
            full_name="Alice Nguyen",
        ),
        User(
            email="bob@example.com",
            hashed_password="dummy_hashed_password_bob",
            full_name="Bob Tran",
        ),
        User(
            email="charlie@example.com",
            hashed_password="dummy_hashed_password_charlie",
            full_name="Charlie Pham",
        ),
        User(
            email="david@example.com",
            hashed_password="dummy_hashed_password_david",
            full_name="David Le",
        ),
    ]
    db.add_all(users)


def seed_menu(db: Session) -> None:
    if db.query(Category).first():
        return

    # 1. Categories
    main_dishes = Category(name="Món Chính", description="Các món đặc sản của Thang Food")
    drinks = Category(name="Đồ uống", description="Nước giải khát đi kèm")
    db.add_all([main_dishes, drinks])
    db.flush()

    # 2. Menu items (4 Món Chính - Iron-clad Whitelist)
    com_tam = MenuItem(
        category_id=main_dishes.id,
        name="Cơm Tấm",
        description="Cơm tấm sườn nướng than hoa, bì, chả, mỡ hành",
        price=55000,
        is_available=True,
    )
    bun_bo = MenuItem(
        category_id=main_dishes.id,
        name="Bún Bò",
        description="Bún bò Huế đầy đủ nạm, gân, giò heo",
        price=60000,
        is_available=True,
    )
    pho = MenuItem(
        category_id=main_dishes.id,
        name="Phở",
        description="Phở bò tái nạm nước dùng hầm xương 24h",
        price=60000,
        is_available=True,
    )
    mi_quang = MenuItem(
        category_id=main_dishes.id,
        name="Mì Quảng",
        description="Mì Quảng tôm thịt trứng, bánh đa giòn rụm",
        price=55000,
        is_available=True,
    )

    db.add_all([com_tam, bun_bo, pho, mi_quang])
    db.flush()

    # 3. Options (Topping & Tùy chỉnh)
    
    # --- Options cho Cơm Tấm ---
    com_tam_topping = ItemOptionGroup(
        item_id=com_tam.id, name="Topping Thêm", is_required=False, multi_select=True
    )
    com_tam_req = ItemOptionGroup(
        item_id=com_tam.id, name="Yêu cầu đặc biệt", is_required=False, multi_select=True
    )
    db.add_all([com_tam_topping, com_tam_req])
    db.flush()

    db.add_all([
        ItemOption(group_id=com_tam_topping.id, name="Trứng ốp la", extra_price=5000),
        ItemOption(group_id=com_tam_topping.id, name="Chả trứng thêm", extra_price=10000),
        ItemOption(group_id=com_tam_topping.id, name="Cơm thêm", extra_price=5000),
        ItemOption(group_id=com_tam_req.id, name="Không mỡ hành", extra_price=0),
        ItemOption(group_id=com_tam_req.id, name="Nước mắm cay", extra_price=0),
    ])


    pho_topping = ItemOptionGroup(
        item_id=pho.id, name="Món ăn kèm", is_required=False, multi_select=True
    )
    pho_req = ItemOptionGroup(
        item_id=pho.id, name="Rau & Gia vị", is_required=False, multi_select=True
    )
    db.add_all([pho_topping, pho_req])
    db.flush()

    db.add_all([
        ItemOption(group_id=pho_topping.id, name="Quẩy giòn", extra_price=5000),
        ItemOption(group_id=pho_topping.id, name="Trứng chần", extra_price=10000),
        ItemOption(group_id=pho_topping.id, name="Thêm bò tái", extra_price=20000),
        ItemOption(group_id=pho_req.id, name="Không hành", extra_price=0),
        ItemOption(group_id=pho_req.id, name="Nước béo", extra_price=0),
    ])

    # --- Options cho Bún Bò ---
    bun_bo_topping = ItemOptionGroup(
        item_id=bun_bo.id, name="Thêm nhân", is_required=False, multi_select=True
    )
    db.add_all([bun_bo_topping])
    db.flush()
    
    db.add_all([
        ItemOption(group_id=bun_bo_topping.id, name="Thêm chả cua", extra_price=15000),
        ItemOption(group_id=bun_bo_topping.id, name="Thêm giò heo", extra_price=15000),
        ItemOption(group_id=bun_bo_topping.id, name="Không tiết", extra_price=0),
    ])
    
    # --- Options cho Mì Quảng ---
    mi_quang_topping = ItemOptionGroup(
        item_id=mi_quang.id, name="Ăn kèm", is_required=False, multi_select=True
    )
    db.add_all([mi_quang_topping])
    db.flush()
    
    db.add_all([
        ItemOption(group_id=mi_quang_topping.id, name="Bánh đa thêm", extra_price=5000),
        ItemOption(group_id=mi_quang_topping.id, name="Nhiều rau sống", extra_price=0),
        ItemOption(group_id=mi_quang_topping.id, name="Thêm tôm", extra_price=15000),
    ])


def seed_faqs(db: Session) -> None:
    if db.query(FAQ).first():
        return

    faqs = [
        FAQ(
            question="Nhà hàng chuyên phục vụ món gì?",
            answer="Thang Food chuyên phục vụ 4 món đặc sản: Cơm Tấm, Bún Bò, Phở và Mì Quảng.",
            tags="menu,mon_an",
        ),
        FAQ(
            question="Giờ mở cửa của quán là khi nào?",
            answer="Quán mở cửa từ 6h00 sáng đến 22h00 tối mỗi ngày để phục vụ cả ăn sáng và ăn tối.",
            tags="gio_mo_cua,thoi_gian",
        ),
        FAQ(
            question="Quán có giao hàng khu vực nào?",
            answer="Hiện tại quán giao hàng trong bán kính 10km.",
            tags="giao_hang,khu_vuc",
        ),
        FAQ(
            question="Chính sách hủy đơn như thế nào?",
            answer="Bạn chỉ có thể hủy đơn khi trạng thái là 'Chờ xác nhận' (Pending). Khi bếp đã nấu, không thể hủy.",
            tags="huy_don,chinhsach",
        ),
    ]
    db.add_all(faqs)


def seed_all() -> None:
    init_db()
    with get_session() as db:
        seed_users(db)
        seed_menu(db)
        seed_faqs(db)


def main() -> None:
    seed_all()


if __name__ == "__main__":
    main()