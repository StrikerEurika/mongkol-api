from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.models.sale import SaleStatus, PaymentMethod

class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    
class SaleItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price_usd: float
    unit_price_khr: float
    subtotal_usd: float
    subtotal_khr: float
    
    class Config:
        from_attributes = True

class SaleCreate(BaseModel):
    sale_datetime: datetime | None = None
    payment_method: PaymentMethod
    discount_amount_usd: float | None = Field(default=None, ge=0)
    discount_amount_khr: float | None = Field(default=None, ge=0)
    note: str | None = None
    items: list[SaleItemCreate] = Field(min_length=1)

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        if not v:
            raise ValueError("សូមជ្រើសរើសទំនិញ (Please select an item)")
        return v
    
class SaleUpdate(BaseModel):
    sale_datetime: datetime | None = None
    payment_method: PaymentMethod | None = None
    discount_amount_usd: float | None = Field(default=None, ge=0)
    discount_amount_khr: float | None = Field(default=None, ge=0)
    note: str | None = None
    
class SaleOut(BaseModel):
    id: int
    sale_datetime: datetime
    total_amount_usd: float
    total_amount_khr: float
    payment_method: PaymentMethod
    discount_amount_usd: float | None
    discount_amount_khr: float | None
    note: str | None
    created_by_user_id: int
    status: SaleStatus
    created_at: datetime
    updated_at: datetime
    
    items: list[SaleItemOut] = []
    
    class Config:
        from_attributes = True