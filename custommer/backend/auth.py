import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import crud
from database import get_db
from security import decode_access_token

# tokenUrl is what Swagger UI's "Authorize" button posts to.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# This service only trusts tokens minted for "customer". A token issued by another
# service has a different "type" claim and is rejected here.
TOKEN_TYPE = "customer"


def get_current_customer(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_exc
    if payload.get("type") != TOKEN_TYPE:
        raise credentials_exc
    subject = payload.get("sub")
    if subject is None:
        raise credentials_exc
    user = crud.get_customer(db, int(subject))
    if user is None or not user.is_active:
        raise credentials_exc
    return user
