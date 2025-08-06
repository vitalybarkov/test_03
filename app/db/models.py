from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key = True, index = True)
    address = Column(String, nullable = False)
    latitude = Column(Float, nullable = False)
    longitude = Column(Float, nullable = False)

    organizations = relationship("Organization", back_populates="building")

class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String, nullable = False)
    parent_id = Column(Integer, ForeignKey("activities.id"), nullable = True)
    level = Column(Integer, default = 1)

    parent = relationship("Activity", remote_side = [id], back_populates = "children")
    children = relationship("Activity", back_populates = "parent")
    organizations = relationship(
        "Organization", 
        secondary = Table(
            "organization_activity",
            Base.metadata,
            Column("organization_id", ForeignKey("organizations.id"), primary_key = True),
            Column("activity_id", ForeignKey("activities.id"), primary_key = True),
        ), 
        back_populates = "activities"
    )

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key = True, index = True)
    name = Column(String, nullable = False)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable = False)

    building = relationship("Building", back_populates = "organizations")
    phone_numbers = relationship("PhoneNumber", back_populates = "organization")
    activities = relationship(
        "Activity", 
        secondary = Table(
            "organization_activity",
            Base.metadata,
            Column("organization_id", ForeignKey("organizations.id"), primary_key = True),
            Column("activity_id", ForeignKey("activities.id"), primary_key = True),
            extend_existing = True
        ), 
        back_populates = "organizations"
    )

class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id = Column(Integer, primary_key = True, index = True)
    number = Column(String, nullable = False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable = False)

    organization = relationship("Organization", back_populates = "phone_numbers")