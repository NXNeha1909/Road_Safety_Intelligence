from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time

# Now importing our advanced MongoDB functions
from database import (
    init_db,
    save_pothole,
    get_all_hazards,
    get_nearby_hazards,
    decay_hazard_confidence,
    report_manual_hazard,
    update_hazard_status,
)
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

# Initialize MongoDB when the app starts
init_db()

# Create an uploads folder to store incoming images
os.makedirs("uploads", exist_ok=True)

# ----------------- API ENDPOINTS -----------------

@app.get("/")
def home():
    return {"message": "Welcome to the AI Road Safety Backend! 🚦 (Now powered by MongoDB)"}

@app.post("/report-hazard")
async def report_hazard(
    lat: float = Form(...),
    lng: float = Form(...),
    image: UploadFile = File(...)
):
    """
    Receives an image and GPS, analyzes via AI.
    Handles Point 5 (Duplicates) & Point 6 (Verification) automatically.
    """
    filename = f"uploads/{int(time.time())}_{image.filename}"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Run AI Model
    ai_result = analyze_image_for_pothole(filename)

    if ai_result["detected"]:
        # POINT 5: Duplicate Control is handled inside save_pothole
        save_result = save_pothole(lat, lng, ai_result["confidence"], filename)
        return JSONResponse({
            "status": "success",
            "message": "Pothole detected and processed!",
            "data": {
                "detected": True,
                "confidence": save_result["confidence"],
                "is_new_hazard": save_result["is_new"],
                "hazard_id": save_result["id"],
            }
        })
    else:
        # POINT 6: Hazard Verification (Decay)
        # If road is clear, we decrease confidence of any expected potholes nearby
        decay_hazard_confidence(lat, lng)
        return JSONResponse({
            "status": "clear",
            "message": "No pothole detected. Hazard verification updated.",
            "data": {
                "detected": False,
                "confidence": ai_result["confidence"],
            }
        })

@app.post("/report-hazard-manual")
async def report_hazard_manual(
    lat: float = Form(...),
    lng: float = Form(...),
    hazard_type: str = Form("pothole"),
    note: str = Form("")
):
    """
    TASK 6: Manual hazard reporting.
    Lets a user flag a hazard directly from their current location
    without going through AI detection.
    """
    result = report_manual_hazard(lat, lng, hazard_type, note)
    return JSONResponse({
        "status": "success",
        "message": "Thanks — your report has been added to the hazard map.",
        "data": result
    })

@app.post("/resolve-hazard/{hazard_id}")
def resolve_hazard(hazard_id: str, action: str = Form(...)):
    """
    TASK 6: Let users flag an existing hazard as "fixed" (repaired) or
    "wrong" (bad detection). action must be one of: fixed, wrong.
    """
    if action not in ("fixed", "wrong"):
        return JSONResponse(
            {"status": "error", "message": "action must be 'fixed' or 'wrong'"},
            status_code=400
        )

    new_status = "resolved" if action == "fixed" else "wrong"
    updated = update_hazard_status(hazard_id, new_status)

    if not updated:
        return JSONResponse(
            {"status": "error", "message": "Hazard not found"},
            status_code=404
        )

    return JSONResponse({
        "status": "success",
        "message": "Hazard marked as fixed and removed from the map." if action == "fixed"
                    else "Hazard removed — thanks for the correction.",
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
    Backend uses MongoDB's native geospatial engine to check 200m radius.
    """
    nearby_hazards = get_nearby_hazards(lat, lng, max_distance_meters=200)

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
