import fastapi
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
from typing import List
import pandas as pd
import joblib
import os
from challenge.model import DelayModel

app = fastapi.FastAPI()

# Initialize model
model = DelayModel()

class Flight(BaseModel):
    OPERA: str
    TIPOVUELO: str
    MES: int

    @validator('MES')
    def check_month(cls, v):
        if not (1 <= v <= 12):
            # This raises a ValueError, which Pydantic catches as a validation error (422).
            # The custom exception handler below will convert it to 400.
            raise ValueError("Month must be between 1 and 12")
        return v

    @validator('TIPOVUELO')
    def check_type(cls, v):
        if v not in ['N', 'I']:
            raise ValueError("TIPOVUELO must be 'N' or 'I'")
        return v
 
class FlightList(BaseModel):
    flights: List[Flight]

class PredictionResponse(BaseModel):
    predict: List[int]

# --- CUSTOM EXCEPTION HANDLER ---
# return 400 Bad Request as expected by the challenge tests.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: fastapi.Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"message": "Invalid data", "details": exc.errors()},
    )

@app.get("/health", status_code=200)
async def get_health():
    return {
        "status": "OK"
    }

@app.post("/predict", status_code=200, response_model=PredictionResponse)
async def post_predict(data: FlightList) -> dict:
    
    # Flatten the list of flights into a DataFrame
    # We process all flights in the batch
    rows = []
    for flight in data.flights:
        rows.append({
            "OPERA": flight.OPERA,
            "TIPOVUELO": flight.TIPOVUELO,
            "MES": flight.MES
        })
    
    df = pd.DataFrame(rows)

    try:
        # Preprocess the batch
        features = model.preprocess(df)
        
        # Predict for the batch
        predictions = model.predict(features)
        
        return {"predict": predictions}
        
    except Exception as e:
        # If anything goes wrong during prediction logic, return 500 or 400
        raise HTTPException(status_code=500, detail=str(e))