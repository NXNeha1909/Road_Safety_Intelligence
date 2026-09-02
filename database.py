import pymongo
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is not set. Create a .env file (see .env.example) "
        "with MONGO_URI=<your connection string>."
    )

client = pymongo.MongoClient(MONGO_URI)
db = client["road_safety_db"]
potholes_collection = db["potholes"]

CONFIDENCE_INCREMENT = 0.10
CONFIDENCE_DECAY = 0.15
CONFIDENCE_REMOVE_THRESHOLD = 0.20
DUPLICATE_RADIUS_METERS = 15
MANUAL_REPORT_CONFIDENCE = 0.60


def init_db():
    potholes_collection.create_index([("location", pymongo.GEOSPHERE)])
    print("✅ MongoDB Connected & Geospatial Index Ready!")


def _serialize(doc):
    """ Shared shape used everywhere the frontend reads a hazard from. """
    return {
        "id": str(doc["_id"]),
        "_id": str(doc["_id"]),
        "latitude": doc["location"]["coordinates"][1],
        "longitude": doc["location"]["coordinates"][0],
        "confidence": round(doc.get("confidence", 0), 2),
        "hazard_type": doc.get("hazard_type", "pothole"),
        "source": doc.get("source", "ai"),
        "status": doc.get("status", "active"),
        "observation_count": doc.get("observation_count", 1),
        "note": doc.get("note", ""),
        "image_path": doc.get("image_path"),
        "timestamp": doc["timestamp"].isoformat() if doc.get("timestamp") else None,
        "first_detected": doc["first_detected"].isoformat() if doc.get("first_detected") else None,
    }


def get_nearby_hazards(lat: float, lng: float, max_distance_meters=200):
    query = {
        "status": "active",
        "location": {
            "$near": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": max_distance_meters,
            }
        },
    }
    return [_serialize(doc) for doc in potholes_collection.find(query)]


def save_pothole(lat: float, lng: float, confidence: float, image_path: str, hazard_type: str = "pothole"):
    """ POINT 5: DUPLICATE POTHOLE CONTROL """
    nearby = get_nearby_hazards(lat, lng, DUPLICATE_RADIUS_METERS)

    if nearby:
        existing = nearby[0]
        new_conf = min(existing["confidence"] + CONFIDENCE_INCREMENT, 1.0)

        potholes_collection.update_one(
            {"_id": ObjectId(existing["id"])},
            {
                "$set": {
                    "confidence": new_conf,
                    "timestamp": datetime.now(),
                    "status": "active",
                },
                "$inc": {"observation_count": 1},
            },
        )
        print(f"🔄 Duplicate Control: Updated existing hazard. New Confidence: {new_conf}")
        return {"is_new": False, "confidence": new_conf, "id": existing["id"]}
    else:
        pothole_data = {
            "location": {"type": "Point", "coordinates": [lng, lat]},
            "confidence": confidence,
            "hazard_type": hazard_type,
            "source": "ai",
            "status": "active",
            "observation_count": 1,
            "image_path": image_path,
            "timestamp": datetime.now(),
            "first_detected": datetime.now(),
        }
        result = potholes_collection.insert_one(pothole_data)
        print("🆕 New hazard saved to DB.")
        return {"is_new": True, "confidence": confidence, "id": str(result.inserted_id)}


def report_manual_hazard(lat: float, lng: float, hazard_type: str, note: str = ""):
    """ TASK 6: Manual hazard reporting by a user (no AI detection involved). """
    nearby = get_nearby_hazards(lat, lng, DUPLICATE_RADIUS_METERS)

    if nearby:
        existing = nearby[0]
        new_conf = min(existing["confidence"] + CONFIDENCE_INCREMENT, 1.0)
        potholes_collection.update_one(
            {"_id": ObjectId(existing["id"])},
            {
                "$set": {"confidence": new_conf, "timestamp": datetime.now(), "status": "active"},
                "$inc": {"observation_count": 1},
            },
        )
        return {"is_new": False, "confidence": new_conf, "id": existing["id"]}

    pothole_data = {
        "location": {"type": "Point", "coordinates": [lng, lat]},
        "confidence": MANUAL_REPORT_CONFIDENCE,
        "hazard_type": hazard_type,
        "source": "manual",
        "status": "active",
        "observation_count": 1,
        "note": note,
        "image_path": None,
        "timestamp": datetime.now(),
        "first_detected": datetime.now(),
    }
    result = potholes_collection.insert_one(pothole_data)
    print("📝 Manual hazard report saved to DB.")
    return {"is_new": True, "confidence": MANUAL_REPORT_CONFIDENCE, "id": str(result.inserted_id)}


def update_hazard_status(hazard_id: str, new_status: str):
    """ TASK 6: Let users mark a hazard as 'fixed' (resolved) or 'wrong' (dismissed). """
    try:
        oid = ObjectId(hazard_id)
    except InvalidId:
        return False

    if new_status == "wrong":
        result = potholes_collection.delete_one({"_id": oid})
        return result.deleted_count > 0

    result = potholes_collection.update_one(
        {"_id": oid},
        {"$set": {"status": new_status, "timestamp": datetime.now()}},
    )
    return result.matched_count > 0


def decay_hazard_confidence(lat: float, lng: float):
    """ POINT 6: HAZARD VERIFICATION / CONFIDENCE UPDATE """
    nearby = get_nearby_hazards(lat, lng, DUPLICATE_RADIUS_METERS)

    for existing in nearby:
        new_conf = existing["confidence"] - CONFIDENCE_DECAY

        if new_conf < CONFIDENCE_REMOVE_THRESHOLD:
            potholes_collection.update_one(
                {"_id": ObjectId(existing["id"])},
                {"$set": {"confidence": max(new_conf, 0), "status": "resolved", "timestamp": datetime.now()}},
            )
            print("🗑️ Hazard Verification: Confidence dropped below 20%. Marked as resolved (Repaired!).")
        else:
            potholes_collection.update_one(
                {"_id": ObjectId(existing["id"])},
                {"$set": {"confidence": new_conf, "timestamp": datetime.now()}},
            )
            print(f"📉 Hazard Verification: Road clear. Decreased confidence to {new_conf}")


def get_all_hazards():
    return [_serialize(doc) for doc in potholes_collection.find({"status": "active"})]
