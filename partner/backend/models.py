from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from database import Base


class Partner(Base):
    __tablename__ = "partners"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    contact_email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Register the shared catalog + order tables on this service's metadata so
# `Base.metadata.create_all` creates them in the shared database.
from Ashared.domain import (  # noqa: E402,F401
    Product,
    Order,
    OrderItem,
    OrderStatus,
)
