from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
import crud
from auth import get_current_worker
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
    # OAuth2 form sends "username" — we treat it as the worker's email.
    worker = crud.authenticate_worker(db, form_data.username, form_data.password)
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(subject=worker.id, token_type="worker")
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.WorkerOut)
def read_me(current_worker: models.Worker = Depends(get_current_worker)):
    return current_worker


@app.post("/workers/", response_model=schemas.WorkerOut, status_code=201)
def create_worker(worker: schemas.WorkerCreate, db: Session = Depends(get_db)):
    if crud.get_worker_by_email(db, worker.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_worker(db, worker)


@app.get("/workers/", response_model=list[schemas.WorkerOut])
def read_workers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_workers(db, skip, limit)


@app.get("/workers/{worker_id}", response_model=schemas.WorkerOut)
def read_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = crud.get_worker(db, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@app.put("/workers/{worker_id}", response_model=schemas.WorkerOut)
def update_worker(
    worker_id: int, updates: schemas.WorkerUpdate, db: Session = Depends(get_db)
):
    worker = crud.update_worker(db, worker_id, updates)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@app.delete("/workers/{worker_id}", status_code=204)
def delete_worker(worker_id: int, db: Session = Depends(get_db)):
    worker = crud.delete_worker(db, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return None


# ============================ Dispatch (courier) ===============================
# A courier picks from the pool of READY orders, claims one (-> picked_up), and
# finally marks it delivered. All endpoints require worker auth.


@app.get("/orders/available", response_model=list[schemas.OrderOut])
def list_available_orders(
    db: Session = Depends(get_db),
    current_worker: models.Worker = Depends(get_current_worker),
):
    """Unclaimed READY orders waiting for a courier."""
    return crud.get_available_orders(db)


@app.get("/orders/", response_model=list[schemas.OrderOut])
def my_deliveries(
    db: Session = Depends(get_db),
    current_worker: models.Worker = Depends(get_current_worker),
):
    return crud.get_orders_by_worker(db, current_worker.id)


@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_my_delivery(
    order_id: int,
    db: Session = Depends(get_db),
    current_worker: models.Worker = Depends(get_current_worker),
):
    order = crud.get_order(db, order_id)
    if not order or order.worker_id != current_worker.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.post("/orders/{order_id}/accept", response_model=schemas.OrderOut)
def accept_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_worker: models.Worker = Depends(get_current_worker),
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    claimed = crud.accept_order(db, current_worker.id, order)
    if not claimed:
        # Not READY, or another courier already claimed it.
        raise HTTPException(
            status_code=409, detail="Order is not available to accept"
        )
    return claimed


@app.get("/dispatch/pings", response_model=list[schemas.CourierPingOut])
def list_dispatch_pings(
    db: Session = Depends(get_db),
    current_worker: models.Worker = Depends(get_current_worker),
):
    """Heads-up pings: orders a partner just accepted. A courier can use these to
    start heading to the delivery address before the order is marked READY."""
    return crud.get_courier_pings(db)


@app.post("/dispatch/pings/{ping_id}/ack", response_model=schemas.CourierPingOut)
def ack_dispatch_ping(
    ping_id: int,
    db: Session = Depends(get_db),
    current_worker: models.Worker = Depends(get_current_worker),
):
    """Dismiss a ping once a courier has seen/handled it."""
    ping = crud.get_courier_ping(db, ping_id)
    if not ping:
        raise HTTPException(status_code=404, detail="Ping not found")
    return crud.acknowledge_ping(db, ping)


@app.post("/orders/{order_id}/deliver", response_model=schemas.OrderOut)
def deliver_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_worker: models.Worker = Depends(get_current_worker),
):
    order = crud.get_order(db, order_id)
    if not order or order.worker_id != current_worker.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != models.OrderStatus.PICKED_UP.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot deliver an order with status '{order.status}'",
        )
    return crud.mark_delivered(db, order)
