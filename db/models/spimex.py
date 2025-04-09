from datetime import date, datetime

from sqlalchemy import Integer, String, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Spimex(Base):
    __tablename__ = "spimex"

    exchange_product_id: Mapped[str]
    exchange_product_name: Mapped[str]
    oil_id: Mapped[str] = mapped_column(String(4))
    delivery_basis_id: Mapped[str] = mapped_column(String(3))
    delivery_basis_name: Mapped[str]
    delivery_type_id: Mapped[str] = mapped_column(String(1))
    volume: Mapped[float]
    total: Mapped[float]
    count: Mapped[float]
    date: Mapped[date]
    created_on: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_on: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
