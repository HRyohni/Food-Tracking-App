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
