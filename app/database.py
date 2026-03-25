from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

# -------------------- LOAD ENV --------------------
load_dotenv()

# -------------------- DATABASE URL --------------------
DATABASE_URL = os.getenv("DATABASE_URL")

# -------------------- ENGINE --------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # prevents timeout errors
    pool_recycle=3600
)

# -------------------- SESSION --------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------- BASE --------------------
Base = declarative_base()

# -------------------- TABLE --------------------
class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)

    model = Column(Integer)
    vehicle_age = Column(Integer)
    km_driven = Column(Integer)

    # ⚠️ MySQL needs length for String
    seller_type = Column(String(50))
    fuel_type = Column(String(50))
    transmission_type = Column(String(50))

    mileage = Column(Float)
    engine = Column(Integer)
    max_power = Column(Float)
    seats = Column(Integer)

    predicted_price = Column(Float)

# -------------------- CREATE TABLE --------------------
def create_tables():
    Base.metadata.create_all(bind=engine)