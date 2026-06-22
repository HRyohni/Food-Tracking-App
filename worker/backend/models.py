from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime

from database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    specialty = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# Register the shared catalog + order tables on this service's metadata so
# couriers can read/update orders from the shared database.
from Ashared.domain import (  # noqa: E402,F401
    Product,
    Order,
    OrderItem,
    OrderStatus,
)
