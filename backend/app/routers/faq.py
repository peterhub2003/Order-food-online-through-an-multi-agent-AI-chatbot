from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.faq import FAQ
from ..schemas.faq import FAQOut


router = APIRouter(tags=["faq"])


@router.get("/faqs", response_model=List[FAQOut])
async def list_faqs(
    q: str | None = Query(default=None, description="Optional search keyword"),
    db: Session = Depends(get_db), 
) -> List[FAQOut]:
    query = db.query(FAQ)

    if q:
        like = f"%{q}%"
        query = query.filter(FAQ.question.ilike(like))

    faqs = query.order_by(FAQ.id).all()
    return [FAQOut.model_validate(f) for f in faqs]
