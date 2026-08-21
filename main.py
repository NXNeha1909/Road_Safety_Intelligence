from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
import math

from database import init_db, save_pothole, get_all_hazards
from ai_model import analyze_image_for_pothole

app = FastAPI(title="Road Safety AI API")

# Allow Frontend to communicate with Backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database when the app starts
init_db()

# Create an uploads folder to store incoming images
os.makedirs("uploads", exist_ok=True)

# ----------------- HELPER FUNCTION (DISTANCE CALCULATION) -----------------
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Haversine Formula: Calculates the distance in METERS between two GPS points.
    """
    R = 6371.0 # Earth radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = R * c
    
    return distance_km * 1000 # Convert to meters

# ----------------- API ENDPOINTS -----------------

@app.get("/")
def home():
    return {"message": "Welcome to the AI Road Safety Backend! 🚦"}

@app.post("/report-hazard")
async def report_hazard(
    lat: float = Form(...),
    lng: float = Form(...),
    image: UploadFile = File(...)
):
    """
    Receives an image and GPS, analyzes via AI, and saves if pothole is found.
    """
    filename = f"uploads/{int(time.time())}_{image.filename}"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Run AI Model
    ai_result = analyze_image_for_pothole(filename)
    
    # Save to Database if pothole is detected
    if ai_result["detected"]:
        save_pothole(lat, lng, ai_result["confidence"], filename)
        return JSONResponse({
            "status": "success",
            "message": "Pothole detected and saved!",
            "data": ai_result
        })
    else:
        return JSONResponse({
            "status": "clear",
            "message": "No pothole detected in this image.",
            "data": ai_result
        })

@app.get("/hazards")
def get_hazards():
    """
    Returns a list of all detected potholes for the Map dashboard.
    """
    hazards = get_all_hazards()
    return {"status": "success", "total": len(hazards), "data": hazards}

@app.get("/check-warning")
def check_warning(lat: float, lng: float):
    """
    LIVE WARNING API:
    Frontend sends the user's current live GPS location here.
    Backend calculates if any pothole is within a 200-meter radius.
    """
    hazards = get_all_hazards()
    nearby_hazards = []
    
    for hazard in hazards:
        # Calculate distance between user and pothole
        distance = calculate_distance(lat, lng, hazard["latitude"], hazard["longitude"])
        
        # If pothole is within 200 meters, add to warning list
        if distance <= 200:
            nearby_hazards.append({
                "distance_meters": round(distance, 2),
                "confidence": hazard["confidence"]
            })
            
    if len(nearby_hazards) > 0:
        return {
            "warning": True,
            "message": f"⚠️ ALERT! {len(nearby_hazards)} pothole(s) detected within 200m ahead. Please slow down.",
            "hazards_nearby": nearby_hazards
        }
    else:
        return {
            "warning": False,
            "message": "Route is clear. No hazards nearby."
        }
