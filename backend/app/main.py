from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from . import models  # noqa: F401
from .routers import auth, faq, menu, orders, users


def init_db() -> None:
    """Create database tables if they do not already exist.

    In a real production setup you would use migrations instead, but for this
    prototype service, automatic table creation keeps things simple.
    """

    Base.metadata.create_all(bind=engine)


app = FastAPI(title="Food Ordering Backend")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:80",  
    "*",                     
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Cho phép các nguồn này gọi API
    allow_credentials=True,      # Cho phép gửi cookie/token
    allow_methods=["*"],         # Quan trọng: Cho phép tất cả method (gồm OPTIONS, POST...)
    allow_headers=["*"],         # Cho phép tất cả header
)

@app.on_event("startup")
async def on_startup() -> None:  # type: ignore[override]
    init_db()


app.include_router(auth.router, prefix="/api")
app.include_router(menu.router, prefix="/api")
app.include_router(faq.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
