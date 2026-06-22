from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Catalog browse (read-only for customers) ----------
class ProductOut(BaseModel):
    id: int
    partner_id: int
    name: str
    description: str | None = None
    price: float
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Placing an order ----------
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    partner_id: int
    delivery_address: str
    items: list[OrderItemCreate]


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit_price: float
    quantity: int

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    customer_id: int
    partner_id: int
    worker_id: int | None = None
    status: str
    delivery_address: str
    total_amount: float
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut]

    class Config:
        from_attributes = True
