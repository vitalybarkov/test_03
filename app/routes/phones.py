from cairo import Status
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app import security
from app.db.session import get_db
from app.db import models, schemas

router = APIRouter(
    prefix = "/phones",
    tags = ["Phones"]
)

## phones

@router.get("/", response_model = list[schemas.PhoneNumberResponse])
def get_phones_numbers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        phones_numbers = db.query(models.PhoneNumber).offset(skip).limit(limit).all()
        if not phones_numbers:
            raise HTTPException(status_code = 404, detail = f"no one phones numbers was not found")
        return phones_numbers
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))