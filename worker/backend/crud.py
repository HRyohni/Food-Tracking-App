from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password, verify_password


def get_worker(db: Session, worker_id: int):
    return db.query(models.Worker).filter(models.Worker.id == worker_id).first()


def get_worker_by_email(db: Session, email: str):
    return db.query(models.Worker).filter(models.Worker.email == email).first()


def get_workers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Worker).offset(skip).limit(limit).all()


def create_worker(db: Session, worker: schemas.WorkerCreate):
    db_worker = models.Worker(
        name=worker.name,
        email=worker.email,
        phone=worker.phone,
        specialty=worker.specialty,
        hashed_password=hash_password(worker.password),
    )
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker


def update_worker(db: Session, worker_id: int, updates: schemas.WorkerUpdate):
    db_worker = get_worker(db, worker_id)
    if not db_worker:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_worker, field, value)
    db.commit()
    db.refresh(db_worker)
    return db_worker


def delete_worker(db: Session, worker_id: int):
    db_worker = get_worker(db, worker_id)
    if not db_worker:
        return None
    db.delete(db_worker)
    db.commit()
    return db_worker


def authenticate_worker(db: Session, email: str, password: str):
    """Return the worker if email+password are valid, else None."""
    user = get_worker_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ---------- Orders (courier dispatch) ----------
def get_available_orders(db: Session, skip: int = 0, limit: int = 100):
    """READY orders not yet claimed by any courier — the dispatch pool."""
    return (
        db.query(models.Order)
        .filter(
            models.Order.status == models.OrderStatus.READY.value,
            models.Order.worker_id.is_(None),
        )
        .order_by(models.Order.created_at.asc())  # oldest first (fair queue)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_orders_by_worker(db: Session, worker_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Order)
        .filter(models.Order.worker_id == worker_id)
        .order_by(models.Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def accept_order(db: Session, worker_id: int, order: models.Order):
    """Claim a READY order: assign this courier and move it to PICKED_UP.

    Returns None if the order was already claimed or isn't READY — the guard is
    what prevents two couriers grabbing the same order.
    """
    if order.status != models.OrderStatus.READY.value or order.worker_id is not None:
        return None
    order.worker_id = worker_id
    order.status = models.OrderStatus.PICKED_UP.value
    db.commit()
    db.refresh(order)
    return order


def mark_delivered(db: Session, order: models.Order):
    order.status = models.OrderStatus.DELIVERED.value
    db.commit()
    db.refresh(order)
    return order


# ---------- Dispatch pings (heads-up when a partner accepts an order) ----------
def get_courier_pings(db: Session, skip: int = 0, limit: int = 100):
    """Un-acknowledged courier pings, newest first."""
    return (
        db.query(models.CourierPing)
        .filter(models.CourierPing.acknowledged.is_(False))
        .order_by(models.CourierPing.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_courier_ping(db: Session, ping_id: int):
    return (
        db.query(models.CourierPing).filter(models.CourierPing.id == ping_id).first()
    )


def acknowledge_ping(db: Session, ping: models.CourierPing):
    """Dismiss a ping so it stops showing in the courier feed."""
    ping.acknowledged = True
    db.commit()
    db.refresh(ping)
    return ping
