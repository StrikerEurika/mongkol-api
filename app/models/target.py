from sqlalchemy import Date, DateTime, Numeric, UniqueConstraint, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Target(Base):
    __tablename__ = "targets"
    __table_args__ = (
        UniqueConstraint("user_id", "period_month", name="uq_target_user_month"),
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    period_month: Mapped[Date] = mapped_column(Date)
    target_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
