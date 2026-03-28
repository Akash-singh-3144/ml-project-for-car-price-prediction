from fastapi import FastAPI, Depends
from pydantic import BaseModel
import pandas as pd
import os
import pickle
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from app.database import SessionLocal, Prediction, create_tables

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.pkl")

def load_model():
    print("Looking for model at:", MODEL_PATH)

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"model.pkl not found at {MODEL_PATH}. Make sure it exists in /models folder."
        )

    # Optional safety check
    with open(MODEL_PATH, "rb") as f:
        header = f.read(10)
        if header.startswith(b"<"):
            raise ValueError("model.pkl is corrupted or not a valid pickle file.")

    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
    except Exception as e:
        raise Exception(f"Error loading model: {str(e)}")

    print("✅ Model loaded successfully!")
    return model


model = None


@app.on_event("startup")
def on_startup():
    global model
    print("🚀 Starting application...")

    create_tables()
    model = load_model()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#input schema
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


@app.get("/")
def home():
    return {"message": "Car Price Prediction API is running 🚀"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None
    }

@app.post("/predict")
def predict(data: CarInput, db: Session = Depends(get_db)):
    try:
        if model is None:
            raise Exception("Model not loaded")

        df = pd.DataFrame([data.model_dump()])
        print("INPUT DF:\n", df)

        prediction = float(model.predict(df)[0])

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
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }