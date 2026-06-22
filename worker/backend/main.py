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
