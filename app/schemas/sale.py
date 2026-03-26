from pydantic import BaseModel, Field
from datetime import datetime
from app.models.sale import SaleStatus, PaymentMethod

class SaleCreate(BaseModel):
    sale_datetime: datetime | None = None
    total_amount: float = Field(gt=0)
    payment_method: PaymentMethod
    discount_amount: float | None = Field(default=None, ge=0)
    note: str | None = None
    
class SaleUpdate(BaseModel):
    sale_datetime: datetime | None = None
    total_amount: float = Field(gt=0)
    payment_method: PaymentMethod
    discount_amount: float | None = Field(default=None, ge=0)
    note: str | None = None
    
class SaleOut(BaseModel):
    id: int
    sale_datetime: datetime
    total_amount: float
    payment_method: PaymentMethod
    discount_amount: float | None
    note: str | None
    createdd_by_user_id: int
    status: SaleStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True