from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.db.models import Building, Activity, Organization, PhoneNumber

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@db:5432/organizations_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

##

def init_db():
    db = SessionLocal()
    
    # создаем здания
    building1 = Building(address = "ул. Ленина, 1", latitude = 55.751244, longitude = 37.618423)
    building2 = Building(address = "пр. Мира, 10", latitude = 55.781244, longitude = 37.638423)
    
    # создаем виды деятельности
    food = Activity(name = "Еда")
    meat = Activity(name = "Мясная продукция", parent = food)
    dairy = Activity(name = "Молочная продукция", parent = food)
    
    # создаем организации
    org1 = Organization(name = "ООО Рога и Копыта", building = building1)
    org1.activities.extend([meat, dairy])
    
    # добавляем и сохраняем
    db.add_all([building1, building2, food, meat, dairy, org1])
    db.commit()
    db.close()