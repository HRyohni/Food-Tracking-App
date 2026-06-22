from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
import crud
from config import settings
from database import engine, get_db

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
