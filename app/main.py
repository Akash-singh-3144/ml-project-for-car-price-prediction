
from fastapi import FastAPI, Depends
from pydantic import BaseModel
import pandas as pd
import os
import pickle
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

# -------------------- APP INIT --------------------
app = FastAPI()

# -------------------- CORS --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -------------------- LOAD MODEL --------------------
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.pkl")

# 🔗 PUT YOUR GOOGLE DRIVE DIRECT DOWNLOAD LINK HERE
MODEL_URL = "https://drive.google.com/file/d/1dXsyh8dZguRwYGy2shvb0qydVmS0SpQY/view?usp=sharing"

def download_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("Downloading model...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Model downloaded successfully!")

# Download if not exists
if not os.path.exists(MODEL_PATH):
    download_model()

print("MODEL PATH:", MODEL_PATH)

# Load model
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)




# -------------------- LOAD MODEL --------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

print("MODEL PATH:", MODEL_PATH)

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)

# -------------------- DATABASE --------------------
from app.database import SessionLocal, Prediction, create_tables

# Create tables on startup
@app.on_event("startup")
def on_startup():
    print("Creating tables if not exist...")
    create_tables()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- INPUT SCHEMA --------------------
class CarInput(BaseModel):
    model: int
    vehicle_age: int
    km_driven: int
    seller_type: str
    fuel_type: str
    transmission_type: str
    mileage: float
    engine: int
    max_power: float
    seats: int

# -------------------- ROOT --------------------
@app.get("/")
def home():
    return {"message": "Car Price Prediction API is running 🚀"}

# -------------------- PREDICTION --------------------
@app.post("/predict")
def predict(data: CarInput, db: Session = Depends(get_db)):
    try:
        # Convert input to DataFrame
        df = pd.DataFrame([data.model_dump()])  # 🔥 better than dict() for pydantic v2
        print("INPUT DF:\n", df)

        # ⚠️ Add encoding here if your model needs it
        # Example:
        # df["fuel_type"] = df["fuel_type"].map({"Petrol": 0, "Diesel": 1, "CNG": 2})

        # Prediction
        prediction = float(model.predict(df)[0])

        # Save to DB
        db_prediction = Prediction(
            model=data.model,
            vehicle_age=data.vehicle_age,
            km_driven=data.km_driven,
            seller_type=data.seller_type,
            fuel_type=data.fuel_type,
            transmission_type=data.transmission_type,
            mileage=data.mileage,
            engine=data.engine,
            max_power=data.max_power,
            seats=data.seats,
            predicted_price=prediction
        )

        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)

        return {
            "success": True,
            "predicted_price": prediction,
            "prediction_id": db_prediction.id
        }

    except Exception as e:
        db.rollback()  # 🔥 important if something fails
        return {
            "success": False,
            "error": str(e)
        }

