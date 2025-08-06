from cairo import Status
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app import security
from app.db.session import get_db
from app.db import models, schemas

router = APIRouter(
    prefix = "/buildings",
    tags = ["Buildings"]
)

## building end-points:

@router.get("/", response_model = list[schemas.Building])
def get_buildings(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_buildings = db.query(models.Building).offset(skip).limit(limit).all()
        if not db_buildings:
            raise HTTPException(status_code = 404, detail = f"no one building was not found")
        return db_buildings
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/{id}", response_model = schemas.Building)  # Changed to single Building
def get_building(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_building = db.query(models.Building).filter(models.Building.id == id).first()
        if not db_building:
            raise HTTPException(status_code = 404, detail = f"building {id} not found")
        return db_building
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.post("/", response_model = schemas.Building)
def create_building(
    building: schemas.BuildingCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_building = models.Building(**building.dict())
        db.add(db_building)
        db.commit()
        db.refresh(db_building)
        return db_building
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.put("/{id}", response_model = schemas.Building)
def update_building(
    id: int,
    building: schemas.BuildingUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_building = db.query(models.Building).filter(models.Building.id == id).first()
        if not db_building:
            raise HTTPException(status_code = 404, detail = f"building {id} not found")
        update_data = building.dict(exclude_unset = True)
        for key, value in update_data.items():
            setattr(db_building, key, value)
        db.commit()
        db.refresh(db_building)
        return db_building
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_building(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_building = db.query(models.Building).filter(models.Building.id == id).first()
        if not db_building:
            raise HTTPException(status_code = Status.HTTP_404_NOT_FOUND, detail=f"Building with ID {id} not found")
        db.delete(db_building)
        db.commit()
        return None
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))