from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class PartnerBase(BaseModel):
    company_name: str
    contact_email: EmailStr
    phone: str | None = None


class PartnerCreate(PartnerBase):
    password: str


class PartnerUpdate(BaseModel):
    company_name: str | None = None
    contact_email: EmailStr | None = None
    phone: str | None = None
    is_active: bool | None = None


class PartnerOut(PartnerBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # ORM mode


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Catalog (Product) — partner-owned ----------
class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float = Field(gt=0)


class ProductCreate(ProductBase):
    is_available: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    is_available: bool | None = None


class ProductOut(ProductBase):
    id: int
    partner_id: int
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Orders (partner view) ----------
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


class OrderStatusUpdate(BaseModel):
    status: str
