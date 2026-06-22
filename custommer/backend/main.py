from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
import crud
from auth import get_current_customer
from config import settings
from database import engine, get_db
from security import create_access_token

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
    # OAuth2 form sends "username" — we treat it as the customer's email.
    customer = crud.authenticate_customer(db, form_data.username, form_data.password)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=customer.id, token_type="customer")
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.CustomerOut)
def read_me(current_customer: models.Customer = Depends(get_current_customer)):
    return current_customer


@app.post("/customers/", response_model=schemas.CustomerOut, status_code=201)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    if crud.get_customer_by_email(db, customer.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_customer(db, customer)


@app.get("/customers/", response_model=list[schemas.CustomerOut])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_customers(db, skip, limit)


@app.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.put("/customers/{customer_id}", response_model=schemas.CustomerOut)
def update_customer(
    customer_id: int, updates: schemas.CustomerUpdate, db: Session = Depends(get_db)
):
    customer = crud.update_customer(db, customer_id, updates)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = crud.delete_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return None


# ============================ Catalog browse (read-only) =======================


@app.get("/products/", response_model=list[schemas.ProductOut])
def browse_products(
    partner_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Available products, optionally filtered to one partner."""
    return crud.list_products(db, partner_id, skip, limit)


@app.get("/products/{product_id}", response_model=schemas.ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ============================ Orders (place + track) ===========================


@app.post("/orders/", response_model=schemas.OrderOut, status_code=201)
def place_order(
    order_in: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_customer: models.Customer = Depends(get_current_customer),
):
    try:
        return crud.create_order(db, current_customer.id, order_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/orders/", response_model=list[schemas.OrderOut])
def my_orders(
    db: Session = Depends(get_db),
    current_customer: models.Customer = Depends(get_current_customer),
):
    return crud.get_orders_by_customer(db, current_customer.id)


@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_my_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_customer: models.Customer = Depends(get_current_customer),
):
    order = crud.get_order(db, order_id)
    if not order or order.customer_id != current_customer.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/orders/{order_id}/cancel", response_model=schemas.OrderOut)
def cancel_my_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_customer: models.Customer = Depends(get_current_customer),
):
    order = crud.get_order(db, order_id)
    if not order or order.customer_id != current_customer.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != models.OrderStatus.PENDING.value:
        raise HTTPException(
            status_code=400, detail="Only pending orders can be cancelled"
        )
    return crud.cancel_order(db, order)
