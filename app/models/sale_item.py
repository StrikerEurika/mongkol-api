from sqlalchemy import Column, Numeric, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    
    quantity: Mapped[int] = mapped_column(default=1)
    
    unit_price_usd: Mapped[float] = mapped_column(Numeric(12, 2))
    unit_price_khr: Mapped[float] = mapped_column(Numeric(12, 2))
    
    subtotal_usd: Mapped[float] = mapped_column(Numeric(12, 2))
    subtotal_khr: Mapped[float] = mapped_column(Numeric(12, 2))

    created_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product")
