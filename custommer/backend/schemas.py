from datetime import datetime

from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None


class CustomerCreate(CustomerBase):
    password: str


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    is_active: bool | None = None


class CustomerOut(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # ORM mode
