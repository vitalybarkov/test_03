import math
import re
from cairo import Status
from fastapi import APIRouter, HTTPException, Query, status
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload
from app.db import models
from app.db import schemas
from . import security
from app.db.session import get_db, engine, init_db
from math import radians, sin, cos, sqrt, atan2
from app.routes import organizations, buildings, activities, phones

models.Base.metadata.create_all(bind = engine)

app = FastAPI(
    title = "Organizations API",
    description = "API for managing organizations, buildings, activities, and phones",
    version = "1.0.0",
    dependencies = [Depends(security.get_api_key)]
)

## root end-points:
@app.get("/")
def read_root():
    return {"message": "Greetings, my friend"}

@app.get("/init/")
def init_data(api_key: str = Depends(security.get_api_key)):
    try:
        init_db()
        return {"message": "the start data was initialized"}
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))
    
# routes
app.include_router(buildings.router)
app.include_router(activities.router)
app.include_router(organizations.router)
app.include_router(phones.router)
