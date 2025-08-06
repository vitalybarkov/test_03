from pydantic import BaseModel, Field
from typing import List, Optional

# building
class BuildingBase(BaseModel):
    address: str = None
    latitude: float = None
    longitude: float = None

class BuildingCreate(BuildingBase):
    pass

class BuildingUpdate(BaseModel):
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class Building(BuildingBase):
    id: int

    class Config:
        from_attributes = True

# activity
class ActivityBase(BaseModel):
    name: str = Field(..., max_length = 100)
    parent_id: Optional[int] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(ActivityBase):
    pass

class ActivityResponse(ActivityBase):
    id: int
    level: int = None

    class Config:
        from_attributes = True

class ActivityTreeResponse(ActivityResponse):
    children: List["ActivityTreeResponse"] = []

ActivityTreeResponse.update_forward_refs()

# phone
class PhoneNumberBase(BaseModel):
    number: str

class PhoneNumberCreate(PhoneNumberBase):
    pass

class PhoneNumberDelete(BaseModel):
    number: Optional[str] = None
    organization_id: Optional[int] = None

class PhoneNumberResponse(PhoneNumberBase):
    id: int
    organization_id: int

    class Config:
        from_attributes = True

# organization
class OrganizationBase(BaseModel):
    name: str = None
    building_id: int = None

class OrganizationCreate(OrganizationBase):
    phone_numbers: List[PhoneNumberBase] = None
    activity_ids: List[int] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    building_id: Optional[int] = None
    activity_ids: Optional[List[int]] = None
    phone_numbers: Optional[List[PhoneNumberBase]] = None

class Organization(OrganizationBase):
    id: int
    phone_numbers: List[str] = None
    activity_ids: List[int] = None
    
    class Config:
        from_attributes = True