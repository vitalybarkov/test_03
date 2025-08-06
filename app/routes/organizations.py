import math
import re
from cairo import Status
from fastapi import APIRouter, HTTPException, Query, status
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app import security
from app.db.session import get_db
from app.db import models, schemas

router = APIRouter(
    prefix = "/organizations",
    tags = ["Organizations"]
)

## organizations end-points

@router.get("/", response_model = list[schemas.Organization])
def get_organizations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        # eager load relationships with pagination
        organizations = (
            db.query(models.Organization)
            .options(
                joinedload(models.Organization.phone_numbers),
                joinedload(models.Organization.activities)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        if not organizations:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "No organizations found")
        # convert each organization to response model
        result = []
        for org in organizations:
            org_response = schemas.Organization(
                id = org.id,
                name = org.name,
                building_id = org.building_id,
                activity_ids = [a.id for a in org.activities],
                phone_numbers = [p.number for p in org.phone_numbers],
            )
            result.append(org_response)
        #
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/{id}", response_model = schemas.Organization)
def get_organizations(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):    
    try:
        # eager load relationships
        db_organizations = (
            db.query(models.Organization)
            .options(
                joinedload(models.Organization.phone_numbers),
                joinedload(models.Organization.activities)
            )
            .filter(models.Organization.id == id)
            .first()
        )
        if not db_organizations:
            raise HTTPException(status_code = 404, detail = f"no one organizations was not found")
        # convert to dict and add activity_ids
        org_dict = {
            **db_organizations.__dict__,
            "activity_ids": [activity.id for activity in db_organizations.activities],
            "phone_numbers": [phone_number.number for phone_number in db_organizations.phone_numbers]
        }
        #
        return schemas.Organization(**org_dict)
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.post("/", response_model = schemas.Organization, status_code = status.HTTP_201_CREATED)
def create_organization(
    organization: schemas.OrganizationBase,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # validate building exists
    if organization.building_id:
        db_building = db.query(models.Building).filter(models.Building.id == organization.building_id).first()
        if not db_building:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"building {organization.building_id} not found")
    # create the new organization
    try:
        db_organization = models.Organization(**organization.dict())
        db.add(db_organization)
        db.commit()
        db.refresh(db_organization)
        return db_organization
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.put("/{id}", response_model = schemas.Organization)
def update_organization(
    id: int,
    organization: schemas.OrganizationBase,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # get the organization with all relationships
    db_organization = (
        db.query(models.Organization)
        .options(
            joinedload(models.Organization.building),
            joinedload(models.Organization.phone_numbers),
            joinedload(models.Organization.activities)
        )
        .filter(models.Organization.id == id)
        .first()
    )
    if not db_organization:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Organization {id} not found")
    # update basic fields if provided
    if organization.name is not None:
        db_organization.name = organization.name
    if organization.building_id is not None:
        # verify building exists
        building = db.query(models.Building).get(organization.building_id)
        if not building:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = f"Building {organization.building_id} not found")
        db_organization.building_id = organization.building_id
    #
    db.commit()
    db.refresh(db_organization)
    #
    result = schemas.Organization(
        id              = db_organization.id,
        name            = db_organization.name,
        building_id     = db_organization.building_id,
        phone_numbers   = [
            schemas.PhoneNumberResponse(
                id              = phone.id,
                number          = phone.number,
                organization_id = phone.organization_id
            ) for phone in db_organization.phone_numbers
        ],
        activity_ids    = [a.id for a in db_organization.activities]
    )
    #
    return result

@router.delete("/{id}", status_code = status.HTTP_204_NO_CONTENT)
def delete_organization(
    id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    try:
        db_organizations = db.query(models.Organization).filter(models.Organization.id == id).first()
        if not db_organizations:
            raise HTTPException(status_code = Status.HTTP_404_NOT_FOUND, detail = f"activity with ID {id} not found")
        db.delete(db_organizations)
        db.commit()
        return None
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.post("/{organization_id}/phones/", response_model = schemas.PhoneNumberResponse)
def add_phone_to_organization(
    organization_id: int,
    phone: schemas.PhoneNumberCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # validate phone number format (basic international format)
    if not re.match(r'^\+?[1-9]\d{1,14}$', phone.number):
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST,detail = "phone number must be in E.164 format (e.g., +1234567890)")
    # check if organization exists
    db_org = db.query(models.Organization).get(organization_id)
    if not db_org:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail=f"organization {organization_id} not found")
    # check if phone number already exists for this organization
    db_phone_number = db.query(models.PhoneNumber).filter(models.PhoneNumber.number == phone.number).first()
    if db_phone_number:
        raise HTTPException(status_code = status.HTTP_409_CONFLICT, detail = f"phone number {phone.number} already exists in the database")
    # create and save new phone number
    db_phone = models.PhoneNumber(
        number          = phone.number,
        organization_id = organization_id
    )
    try:
        db.add(db_phone)
        db.commit()
        db.refresh(db_phone)
        #
        return db_phone
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error saving phone number: {str(e)}")

@router.delete("/phones/")
def remove_phone_from_organization(
    phone: schemas.PhoneNumberDelete,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # validate imput
    if not phone.number and not phone.organization_id:
        raise HTTPException(status_code = 404, detail = f"phone number or organization_id not entered")
    # looking for the phone number existence
    db_phone_number = None
    if phone.number:
        db_phone_number = db.query(models.PhoneNumber).filter(models.PhoneNumber.number == phone.number).first()
    if phone.organization_id:
        db_phone_number = db.query(models.PhoneNumber).filter(models.PhoneNumber.organization_id == phone.organization_id).first()
    if not db_phone_number:
        raise HTTPException(status_code = 404, detail = f"phone number {phone.number} or organization_id {phone.organization_id} not found")
    # deleting the phone number from the database
    try:
        db.delete(db_phone_number)
        db.commit()
        #
        return {"message": f"Phone number {db_phone_number.number} was deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.post("/{organization_id}/activities/{activity_id}")
def add_activity_to_organization(
    organization_id: int,
    activity_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # checking for existence the organization and the activity
    db_organization = db.query(models.Organization).filter(models.Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(status_code = 404, detail = f"organization {organization_id} not found")
    db_activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(status_code = 404, detail = f"activity {db_activity} not found")
    # check if activity is already associated with the organization
    if db_activity in db_organization.activities:
        raise HTTPException(status_code = 400, detail = f"activity {activity_id} is already associated with organization {organization_id}")
    # add the activity in to the organization
    try:
        if db_activity not in db_organization.activities:
            db_organization.activities.append(db_activity)
            db.commit()
        #
        return {"message": f"activity {activity_id} added to organization {organization_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.delete("/{organization_id}/activities/{activity_id}")
def remove_activity(
    organization_id: int,
    activity_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(security.get_api_key)
):
    # checking for existence the organization and the activity
    db_organization = db.query(models.Organization).filter(models.Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(status_code = 404, detail = f"organization {organization_id} not found")
    db_activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not db_activity:
        raise HTTPException(status_code = 404, detail = f"activity {db_activity} not found")
    # delete the activity from the organization
    try:
        if db_activity in db_organization.activities:
            db_organization.activities.remove(db_activity)
            db.commit()
            #
            return {"message": f"activity {activity_id} removed from organization {organization_id}"}
        else:
            #
            return {"message": f"activity {activity_id} not found in the organization {organization_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

## --- Special Endpoints --- ##

@router.get("/by-building/{id}", response_model = list[schemas.Organization])
def get_organizations_by_building_id(id: int, db: Session = Depends(get_db)):
    # get organizations in a specific building
    try:
        db_building = db.query(models.Building).filter(models.Building.id == id).first()
        if not db_building:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"building {id} not found")
        db_organizations = db.query(models.Organization).filter(models.Organization.building_id == id).all()
        if db_organizations is None:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"organization {id} not found")
        return db_organizations
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/by-activity/{id}", response_model = list[schemas.Organization])
def get_organizations_by_activity_id(id: int, db: Session = Depends(get_db)):
    try:
        db_activity = db.query(models.Activity).filter(models.Activity.id == id).first()
        if not db_activity:
            raise HTTPException(status_code = 404, detail = f"activity {id} not found")
        db_organizations = (db.query(models.Organization)
            .join(models.Organization.activities)
            .filter(models.Activity.id == id)
            .all())
        if db_organizations is None:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"no organizations found containing activity {id}")
        return db_organizations
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/by-activity-tree/{activity_id}", response_model = list[schemas.Organization])
def get_organizations_by_activity_tree(
    activity_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all organizations related to an activity and its children (up to 3 levels deep).
    For example, searching for "Food" activity will return organizations with:
    - Food
    - Meat products
    - Dairy products
    - etc. (up to 3 levels deep)
    """
    def get_child_activity_ids(parent_id: int, current_level: int = 1) -> list[int]:
        if current_level > 3:  # limit to 3 levels of nesting
            return []
        child_activities = db.query(models.Activity).filter(models.Activity.parent_id == parent_id).all()
        child_ids = [a.id for a in child_activities]        
        for child_id in child_ids:
            child_ids.extend(get_child_activity_ids(child_id, current_level + 1))

        return child_ids
    try:
        # check if main activity exists
        main_activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
        if not main_activity:
            raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = "activity not found")
        # get all relevant activity IDs (main + children up to 3 levels)
        all_activity_ids = [activity_id] + get_child_activity_ids(activity_id)
        # get organizations for all these activities
        organizations = (
            db.query(models.Organization)
            .join(models.Organization.activities) # use the relationship property
            .filter(models.Activity.id.in_(all_activity_ids)) # filter by activity IDs
            .distinct()
            .all()
        )
        #
        return organizations
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/nearby/", response_model = list[schemas.Organization])
def get_organizations_nearby(
    lat: float = Query(..., example = 40.5, description = "Latitude of center point"),
    lon: float = Query(..., example = 74.0, description = "Longitude of center point"),
    radius: float = Query(..., example = 500.0, description = "Radius in meters"),
    db: Session = Depends(get_db)
):
    try:
        # input validation
        if radius <= 0:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "radius must be positive")
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "Invalid coordinates")
        # haversine distance calculation
        def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            R = 6371000  # earth radius in meters
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            a = (math.sin(delta_phi/2)**2 + 
                math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2)
            return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        # get all organizations with related data
        organizations = (
            db.query(models.Organization)
            .join(models.Building)
            .options(
                joinedload(models.Organization.building),
                joinedload(models.Organization.activities)
            )
            .all()
        )
        # filter organizations within radius
        nearby_orgs = [
            org for org in organizations
            if calculate_distance(lat, lon, org.building.latitude, org.building.longitude) <= radius
        ]
        #
        return nearby_orgs
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/search/within-rectangle", response_model = list[schemas.Organization])
def get_organizations_in_rectangle(
    min_lat: float = Query(..., example = 40.7128, description = "Minimum latitude"),
    min_lon: float = Query(..., example = -74.0060, description = "Minimum longitude"), 
    max_lat: float = Query(..., example = 40.8138, description = "Maximum latitude"),
    max_lon: float = Query(..., example = -73.9060, description = "Maximum longitude"),
    db: Session = Depends(get_db)
):
    try:
        # coordinate validation
        if not (-90 <= min_lat <= 90) or not (-90 <= max_lat <= 90):
            raise HTTPException(400, "latitude must be between -90 and 90")
        if not (-180 <= min_lon <= 180) or not (-180 <= max_lon <= 180):
            raise HTTPException(400, "longitude must be between -180 and 180")
        if min_lat > max_lat or min_lon > max_lon:
            raise HTTPException(400, "min values must be <= max values")
        # query with explicit joins
        result = (
            db.query(models.Organization)
            .join(models.Building)
            .filter(
                models.Building.latitude.between(min_lat, max_lat),
                models.Building.longitude.between(min_lon, max_lon)
            )
            .options(
                joinedload(models.Organization.building),
                joinedload(models.Organization.activities)
            )
            .all()
        )
        #
        return result
    except Exception as e:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))

@router.get("/search/by-name", response_model = list[schemas.Organization])
def search_organizations_by_name(
    name_query: str = Query(..., min_length = 1, max_length = 100, description = "search string for organization name"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        organizations = (
            db.query(models.Organization)
            .filter(models.Organization.name.ilike(f"%{name_query}%"))
            .order_by(models.Organization.name)
            .offset(skip)
            .limit(limit)
            .options(
                joinedload(models.Organization.building),
                joinedload(models.Organization.activities)
            )
            .all()
        )
        #
        return organizations
    except Exception as e:
            raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = str(e))