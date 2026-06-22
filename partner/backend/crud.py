from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password


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
