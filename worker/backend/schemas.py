from datetime import datetime

from pydantic import BaseModel, EmailStr


class WorkerBase(BaseModel):
    name: str
    email: EmailStr
    phone: str | None = None
    specialty: str | None = None


class WorkerCreate(WorkerBase):
    password: str


class WorkerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    specialty: str | None = None
    is_active: bool | None = None


class WorkerOut(WorkerBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # ORM mode


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Orders (worker/courier view) ----------
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
