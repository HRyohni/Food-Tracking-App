"""Cross-actor domain models: the catalog (Product) and the order lifecycle
(Order, OrderItem).

These live in Ashared — not in a single service — because they're referenced by
more than one backend: partners create Products and manage Orders, customers
browse Products and place Orders, and (next step) workers deliver Orders. Every
service registers these on the SAME shared Base/metadata, so there's one
`products` / `orders` / `order_items` table in the shared database.

Cross-actor links (customer_id, partner_id, worker_id) are plain indexed
integers, NOT database ForeignKeys: the customers/partners/workers tables are
each created by their own service, so a hard FK constraint could be built before
its target table exists. We keep referential integrity at the application layer
instead — the standard trade-off for a shared-DB, multi-service setup.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderStatus(str, enum.Enum):
    """The order lifecycle. Stored as its string value in the DB."""

    PENDING = "pending"        # customer placed it, awaiting partner
    ACCEPTED = "accepted"      # partner accepted
    REJECTED = "rejected"      # partner declined (terminal)
    PREPARING = "preparing"    # partner is making it
    READY = "ready"            # ready for a courier to pick up
    PICKED_UP = "picked_up"    # courier has it, en route
    DELIVERED = "delivered"    # delivered to customer (terminal)
    CANCELLED = "cancelled"    # customer cancelled (terminal)


class Product(Base):
    """A catalog/menu item. Owned by exactly one partner."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    # Logical reference -> partners.id (the owner). Only this partner may edit it.
    partner_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class Order(Base):
    """A customer's order from a single partner, delivered by one worker."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, index=True, nullable=False)
    partner_id = Column(Integer, index=True, nullable=False)
    worker_id = Column(Integer, index=True, nullable=True)  # assigned later
    status = Column(
        String, default=OrderStatus.PENDING.value, nullable=False, index=True
    )
    delivery_address = Column(String, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )


class CourierPing(Base):
    """A heads-up dropped into the courier pool the moment a partner ACCEPTS an
    order, so a courier can start heading to the delivery address before the food
    is marked READY.

    It is NOT a hard assignment — there's no assigned courier yet at accept time,
    so any courier can read the ping. A courier dismisses it by setting
    `acknowledged`. `delivery_address` is snapshotted from the order so the
    courier view needs no join and the ping still reads correctly even if the
    order is later edited."""

    __tablename__ = "courier_pings"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, index=True, nullable=False)    # logical ref -> orders.id
    partner_id = Column(Integer, index=True, nullable=False)  # logical ref -> partners.id
    delivery_address = Column(String, nullable=False)         # snapshot from the order
    acknowledged = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class OrderItem(Base):
    """One line in an order. Name/price are SNAPSHOTTED at order time so later
    catalog edits never change a historical order's contents or total."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id = Column(Integer, nullable=False)  # logical ref -> products.id
    product_name = Column(String, nullable=False)  # snapshot
    unit_price = Column(Numeric(10, 2), nullable=False)  # snapshot
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
