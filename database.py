import pymongo
from datetime import datetime

# Tumhara MongoDB connection URL
MONGO_URI = "mongodb+srv://yashmittal30062007_db_user:hKHbOnTQYVnFTXKx@cluster0.hwtyuaj.mongodb.net/?appName=Cluster0"

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client["road_safety_db"]
potholes_collection = db["potholes"]

def init_db():
    """
    Creates a 2dsphere index for ultra-fast location queries.
    This is the "Wow Factor" for judges!
    """
    potholes_collection.create_index([("location", pymongo.GEOSPHERE)])
    print("✅ MongoDB Connected & Geospatial Index Ready!")

def save_pothole(lat: float, lng: float, confidence: float, image_path: str):
    """
    Saves the pothole in GeoJSON format.
    """
    pothole_data = {
        "location": {
            "type": "Point",
            "coordinates": [lng, lat] # MongoDB always expects Longitude first, then Latitude
        },
        "confidence": confidence,
        "image_path": image_path,
        "timestamp": datetime.now()
    }
    potholes_collection.insert_one(pothole_data)

def get_all_hazards():
    """
    Fetches all potholes for the Live Map.
    """
    hazards = []
    for doc in potholes_collection.find():
        hazards.append({
            "id": str(doc["_id"]),
            "latitude": doc["location"]["coordinates"][1],
            "longitude": doc["location"]["coordinates"][0],
            "confidence": doc["confidence"],
            "image_path": doc["image_path"],
            "timestamp": doc["timestamp"].isoformat()
        })
    return hazards

def get_nearby_hazards(lat: float, lng: float, max_distance_meters=200):
    """
    Uses MongoDB's native $near query to find potholes within 200m.
    No manual math needed anymore!
    """
    query = {
        "location": {
            "$near": {
                "$geometry": {
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                "$maxDistance": max_distance_meters
            }
        }
    }
    
    nearby = []
    for doc in potholes_collection.find(query):
        nearby.append({
            "latitude": doc["location"]["coordinates"][1],
            "longitude": doc["location"]["coordinates"][0],
            "confidence": doc["confidence"]
        })
    return nearby
