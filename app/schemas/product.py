from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class ProductCreate(BaseModel):
    name_km: str = Field(..., min_length=1)
    name_en: str = Field(..., min_length=1)
    description: str | None = None
    price_usd: float = Field(default=0, ge=0)
    price_khr: float = Field(default=0, ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("name_km")
    @classmethod
    def validate_name_km(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("សូមបញ្ចូលឈ្មោះទំនិញ (Please enter a product name)")
        return v
        
    @field_validator("price_usd", "price_khr")
    @classmethod
    def validate_price(cls, v: float) -> float:
        if v < 0:
            raise ValueError("សូមបញ្ចូលតម្លៃឲ្យបានត្រឹមត្រូវ (Please enter a valid price)")
        return v

class ProductUpdate(BaseModel):
    name_km: str | None = Field(default=None, min_length=1)
    name_en: str | None = Field(default=None, min_length=1)
    description: str | None = None
    price_usd: float | None = Field(default=None, ge=0)
    price_khr: float | None = Field(default=None, ge=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None

class ProductOut(BaseModel):
    id: int
    name_km: str
    name_en: str
    description: str | None
    price_usd: float
    price_khr: float
    stock_quantity: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
