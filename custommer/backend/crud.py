from sqlalchemy.orm import Session

import models
import schemas
from security import hash_password, verify_password


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


def authenticate_customer(db: Session, email: str, password: str):
    """Return the customer if email+password are valid, else None."""
    user = get_customer_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ---------- Catalog browse (read-only) ----------
def list_products(db: Session, partner_id: int | None = None, skip: int = 0, limit: int = 100):
    query = db.query(models.Product).filter(models.Product.is_available.is_(True))
    if partner_id is not None:
        query = query.filter(models.Product.partner_id == partner_id)
    return query.offset(skip).limit(limit).all()


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


# ---------- Orders (customer side: place + track) ----------
def create_order(db: Session, customer_id: int, order_in: schemas.OrderCreate):
    """Build an order from a single partner's products. Raises ValueError on any
    invalid item; price/name are snapshotted and the total computed here."""
    if not order_in.items:
        raise ValueError("Order must contain at least one item")

    db_order = models.Order(
        customer_id=customer_id,
        partner_id=order_in.partner_id,
        delivery_address=order_in.delivery_address,
        status=models.OrderStatus.PENDING.value,
        total_amount=0,
    )

    total = 0.0
    for item in order_in.items:
        product = get_product(db, item.product_id)
        if not product:
            raise ValueError(f"Product {item.product_id} not found")
        if product.partner_id != order_in.partner_id:
            raise ValueError(
                f"Product {item.product_id} does not belong to partner "
                f"{order_in.partner_id}"
            )
        if not product.is_available:
            raise ValueError(f"Product '{product.name}' is not available")
        db_order.items.append(
            models.OrderItem(
                product_id=product.id,
                product_name=product.name,
                unit_price=product.price,
                quantity=item.quantity,
            )
        )
        total += float(product.price) * item.quantity

    db_order.total_amount = total
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


def get_orders_by_customer(db: Session, customer_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(models.Order)
        .filter(models.Order.customer_id == customer_id)
        .order_by(models.Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def cancel_order(db: Session, order: models.Order):
    order.status = models.OrderStatus.CANCELLED.value
    db.commit()
    db.refresh(order)
    return order
