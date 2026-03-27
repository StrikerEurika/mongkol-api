from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models.user import UserRole

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    can_refund: bool | None = None

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    can_refund: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
