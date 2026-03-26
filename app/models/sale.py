import enum
from sqlalchemy import Boolean, Column, Enum, String, func, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class SaleStatus(enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    LOCKED = "locked"


class PaymentMethod(enum.Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    EWALLET = "ewallet"


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_datetime: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    payment_method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod))
    discount_amount: Mapped[float | None] = mapped_column(
        Numeric(12, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True)
    status: Mapped[SaleStatus] = mapped_column(
        Enum(SaleStatus), default=SaleStatus.DRAFT, index=True)

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    created_by = relationship("User")
