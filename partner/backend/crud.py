from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password, verify_password


def get_partner(db: Session, partner_id: int):
    return db.query(models.Partner).filter(models.Partner.id == partner_id).first()


def get_partner_by_email(db: Session, contact_email: str):
    return (
        db.query(models.Partner)
        .filter(models.Partner.contact_email == contact_email)
        .first()
    )


def get_partners(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Partner).offset(skip).limit(limit).all()


def create_partner(db: Session, partner: schemas.PartnerCreate):
    db_partner = models.Partner(
        company_name=partner.company_name,
        contact_email=partner.contact_email,
        phone=partner.phone,
        hashed_password=hash_password(partner.password),
    )
    db.add(db_partner)
    db.commit()
    db.refresh(db_partner)
    return db_partner


def update_partner(db: Session, partner_id: int, updates: schemas.PartnerUpdate):
    db_partner = get_partner(db, partner_id)
    if not db_partner:
        return None
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_partner, field, value)
    db.commit()
    db.refresh(db_partner)
    return db_partner


def delete_partner(db: Session, partner_id: int):
    db_partner = get_partner(db, partner_id)
    if not db_partner:
        return None
    db.delete(db_partner)
    db.commit()
    return db_partner


def authenticate_partner(db: Session, email: str, password: str):
    """Return the partner if email+password are valid, else None."""
    user = get_partner_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ---------- Catalog (Product) — owned by the partner ----------
def create_product(db: Session, partner_id: int, product: schemas.ProductCreate):
    db_product = models.Product(
        partner_id=partner_id,
        name=product.name,
        description=product.description,
        price=product.price,
        is_available=product.is_available,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products_by_partner(db: Session, partner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Product)
        .filter(models.Product.partner_id == partner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_available_products(db: Session, partner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Product)
        .filter(
            models.Product.partner_id == partner_id,
            models.Product.is_available.is_(True),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def update_product(db: Session, partner_id: int, product_id: int, updates: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product or db_product.partner_id != partner_id:
        return None  # not found OR not owned by this partner
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, partner_id: int, product_id: int):
    db_product = get_product(db, product_id)
    if not db_product or db_product.partner_id != partner_id:
        return None
    db.delete(db_product)
    db.commit()
    return db_product


# ---------- Orders (partner side: read + status transitions) ----------
def get_orders_by_partner(db: Session, partner_id: int, status: str | None = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Order).filter(models.Order.partner_id == partner_id)
    if status:
        query = query.filter(models.Order.status == status)
    return (
        query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()
    )


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def set_order_status(db: Session, order: models.Order, new_status: str):
    order.status = new_status
    db.commit()
    db.refresh(order)
    return order
