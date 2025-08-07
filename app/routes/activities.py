from cairo import Status
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app import security
from app.db.session import get_db
from app.db import models, schemas

router = APIRouter(
    prefix = "/activities",
    tags = ["Activities"]
)

## activities end-points

@router.get("/", response_model = list[schemas.ActivityResponse])
def get_activities(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        activities = db.query(models.Activity).offset(skip).limit(limit).all()
        if not activities:
            raise HTTPException(status_code = 404, detail = f"no one activities was not found")
        #
        return activities
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/{id}", response_model = schemas.ActivityResponse)
def get_activity(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_activity = db.query(models.Activity).filter(models.Activity.id == id).first()
        if db_activity is None:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"activity {id} not found")
        #
        return db_activity
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/{id}/tree", response_model = schemas.ActivityTreeResponse)
def get_activity_tree(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        # prevent circular reference
        db_activity = db.query(models.Activity).filter(models.Activity.id == id).first()
        if db_activity is None:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"activity {id} not found")
        if db_activity.parent_id == db_activity.id:
            db_activity.parent_id = None
            db.commit()
            db.refresh(db_activity)
        #
        db_activity = db.query(models.Activity).options(joinedload(models.Activity.children)).filter(models.Activity.id == id).first()
        #
        return db_activity
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.post("/", response_model = schemas.ActivityResponse, status_code = status.HTTP_201_CREATED)
def create_activity(
    activity: schemas.ActivityCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # validate parent exists and level < 3
    if activity.parent_id:
        parent = db.query(schemas.Activity).filter(schemas.Activity.id == activity.parent_id).first()
        if not parent:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "parent activity not found")
        if parent.level >= 3:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "maximum nesting level is 3")
    # create the new activity
    try:
        db_activity = models.Activity(**activity.dict())
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        #
        return db_activity
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.put("/{id}", response_model = schemas.ActivityResponse)
def update_activity(
    id: int,
    activity: schemas.ActivityUpdate,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # checking for the activity
    db_activity = db.query(schemas.Activity).filter(schemas.Activity.id == id).first()
    if db_activity is None:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"activity {id} not found")
    # validate parent changes
    if activity.parent_id and activity.parent_id != db_activity.parent_id:
        new_parent = db.query(schemas.Activity).filter(schemas.Activity.id == activity.parent_id).first()
        if not new_parent:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = f"new parent activity not found")
        if new_parent.level >= 3:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = f"cannot move to parent with level 3 or higher")
    # update activity information
    try:
        db_activity = db.query(models.Activity).filter(models.Activity.id == id).first()
        if not db_activity:
            raise HTTPException(status_code = 404, detail = f"activity {id} not found")
        update_data = activity.dict(exclude_unset = True)
        for key, value in update_data.items():
            setattr(db_activity, key, value)
        db.commit()
        db.refresh(db_activity)
        #
        return db_activity
    except Exception as e:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_activity(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_activity = db.query(models.Activity).filter(models.Activity.id == id).first()
        if not db_activity:
            raise HTTPException(status_code = Status.HTTP_404_NOT_FOUND, detail = f"activity with ID {id} not found")
        db.delete(db_activity)
        db.commit()
        #
        return None
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))