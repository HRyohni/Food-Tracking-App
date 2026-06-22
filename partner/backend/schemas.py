from datetime import datetime

from pydantic import BaseModel, EmailStr


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
