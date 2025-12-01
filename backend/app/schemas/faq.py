from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FAQOut(BaseModel):
    id: int
    question: str
    answer: str
    tags: str | None = None

    model_config = ConfigDict(from_attributes=True)
