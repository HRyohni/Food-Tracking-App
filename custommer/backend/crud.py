from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password


def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()


def get_customer_by_email(db: Session, email: str):
    return db.query(models.Customer).filter(models.Customer.email == email).first()


def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).offset(skip).limit(limit).all()


def create_customer(db: Session, customer: schemas.CustomerCreate):
    db_customer = models.Customer(
        name=customer.name,
        email=customer.email,
        phone=customer.phone,
        hashed_password=hash_password(customer.password),
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def update_customer(db: Session, customer_id: int, updates: schemas.CustomerUpdate):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_customer, field, value)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def delete_customer(db: Session, customer_id: int):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    db.delete(db_customer)
    db.commit()
    return db_customer
