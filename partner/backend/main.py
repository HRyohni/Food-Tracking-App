from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
import crud
from auth import get_current_partner
from config import settings
from database import engine, get_db
from models import OrderStatus
from security import create_access_token

# Status changes a partner is allowed to make, keyed by the order's current
# status. Anything not listed here is rejected with 400.
PARTNER_TRANSITIONS = {
    OrderStatus.PENDING.value: {OrderStatus.ACCEPTED.value, OrderStatus.REJECTED.value},
    OrderStatus.ACCEPTED.value: {OrderStatus.PREPARING.value},
    OrderStatus.PREPARING.value: {OrderStatus.READY.value},
}

models.Base.metadata.create_all(bind=engine)  # creates tables

app = FastAPI(title=settings.APP_TITLE)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # OAuth2 form sends "username" — we treat it as the partner's contact_email.
    partner = crud.authenticate_partner(db, form_data.username, form_data.password)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=partner.id, token_type="partner")
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.PartnerOut)
def read_me(current_partner: models.Partner = Depends(get_current_partner)):
    return current_partner


@app.post("/partners/", response_model=schemas.PartnerOut, status_code=201)
def create_partner(partner: schemas.PartnerCreate, db: Session = Depends(get_db)):
    if crud.get_partner_by_email(db, partner.contact_email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_partner(db, partner)


@app.get("/partners/", response_model=list[schemas.PartnerOut])
def read_partners(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_partners(db, skip, limit)


@app.get("/partners/{partner_id}", response_model=schemas.PartnerOut)
def read_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = crud.get_partner(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner


@app.put("/partners/{partner_id}", response_model=schemas.PartnerOut)
def update_partner(
    partner_id: int, updates: schemas.PartnerUpdate, db: Session = Depends(get_db)
):
    partner = crud.update_partner(db, partner_id, updates)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return partner


@app.delete("/partners/{partner_id}", status_code=204)
def delete_partner(partner_id: int, db: Session = Depends(get_db)):
    partner = crud.delete_partner(db, partner_id)
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    return None


# ============================ Catalog (partner-owned) ============================
# Only the authenticated partner can create/manage their own products.


@app.post("/products/", response_model=schemas.ProductOut, status_code=201)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_partner: models.Partner = Depends(get_current_partner),
):
    return crud.create_product(db, current_partner.id, product)


@app.get("/products/", response_model=list[schemas.ProductOut])
def list_my_products(
    db: Session = Depends(get_db),
    current_partner: models.Partner = Depends(get_current_partner),
):
    return crud.get_products_by_partner(db, current_partner.id)


@app.put("/products/{product_id}", response_model=schemas.ProductOut)
def update_product(
    product_id: int,
    updates: schemas.ProductUpdate,
    db: Session = Depends(get_db),
    current_partner: models.Partner = Depends(get_current_partner),
):
    product = crud.update_product(db, current_partner.id, product_id, updates)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_partner: models.Partner = Depends(get_current_partner),
):
    product = crud.delete_product(db, current_partner.id, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return None


@app.get("/partners/{partner_id}/products", response_model=list[schemas.ProductOut])
def browse_partner_menu(partner_id: int, db: Session = Depends(get_db)):
    """Public: a partner's available menu, for customers to browse."""
    return crud.get_available_products(db, partner_id)


# ============================ Orders (partner manages) ==========================


@app.get("/orders/", response_model=list[schemas.OrderOut])
def list_partner_orders(
    status: str | None = None,
    db: Session = Depends(get_db),
    current_partner: models.Partner = Depends(get_current_partner),
):
    return crud.get_orders_by_partner(db, current_partner.id, status)


@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_partner_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_partner: models.Partner = Depends(get_current_partner),
):
    order = crud.get_order(db, order_id)
    if not order or order.partner_id != current_partner.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/orders/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(
    order_id: int,
    payload: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_partner: models.Partner = Depends(get_current_partner),
):
    order = crud.get_order(db, order_id)
    if not order or order.partner_id != current_partner.id:
        raise HTTPException(status_code=404, detail="Order not found")
    allowed = PARTNER_TRANSITIONS.get(order.status, set())
    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from '{order.status}' to '{payload.status}'",
        )
    return crud.set_order_status(db, order, payload.status)
