from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password


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
