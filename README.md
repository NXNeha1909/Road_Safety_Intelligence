# DriveSafe AI (Backend)

This is the FastAPI backend for the Road Safety Hackathon project, **DriveSafe AI**.
It receives road images, analyzes them for potholes using a YOLO model, and stores
hazard locations in MongoDB (with geospatial queries for nearby-hazard checks).

## 🚀 How to Run the Server

1. Open your terminal in this folder.
2. Copy `.env.example` to `.env` and set your own MongoDB connection string:
   ```bash
   cp .env.example .env
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
5. Open the Interactive API Docs (Swagger UI) in your browser:
   👉 **http://127.0.0.1:8000/docs**

The `.env` file is never committed — it's already covered by `.gitignore`.

---

## 🔌 API Endpoints (For Frontend Developer)

### 1. Upload & Analyze Image
* **URL**: `POST /report-hazard`
* **Content-Type**: `multipart/form-data`
* **Body Parameters**:
  * `lat` (float): Latitude of the device
  * `lng` (float): Longitude of the device
  * `image` (file): The photo captured by the user
* **Response**: `{ status, message, data: { detected, confidence, is_new_hazard, hazard_id } }`

### 2. Get All Hazards for Map
* **URL**: `GET /hazards`
* **Response**: `{ status, total, data: [...] }` — each hazard includes `latitude`,
  `longitude`, `confidence`, `hazard_type`, `source`, `status`, `observation_count`,
  `image_path`, and `timestamp`. Use this to plot red markers on the Leaflet.js map.

### 3. Check for Nearby Hazards (live warnings)
* **URL**: `GET /check-warning?lat=...&lng=...`
* **Response**: `{ warning: bool, message, hazards_nearby }` — checks a 200m radius
  around the given point using MongoDB's geospatial index. Used by both Driving
  Mode and Navigate Only Mode.

### 4. Report a Hazard Manually
* **URL**: `POST /report-hazard-manual`
* **Content-Type**: `multipart/form-data`
* **Body Parameters**: `lat`, `lng`, `hazard_type` (`pothole` / `water_logging` /
  `construction` / `other`), `note` (optional)
* **Response**: `{ status, message, data: { is_new, confidence, id } }`

### 5. Mark a Hazard as Fixed or Wrong
* **URL**: `POST /resolve-hazard/{hazard_id}`
* **Body Parameters**: `action` — `fixed` (marks resolved, removed from `/hazards`)
  or `wrong` (deletes the report entirely)
* **Response**: `{ status, message }`

---

## 🧠 Hazard Reliability Logic

* **Duplicate control**: a new detection within 15m of an existing hazard bumps its
  confidence by +10% (capped at 100%) and increments `observation_count`, instead of
  creating a new entry.
* **Confidence decay**: if the AI scans a location and finds no pothole, any existing
  hazard within 15m loses 15% confidence. Below 20% confidence, it's marked `resolved`
  (assumed repaired) and drops off the map.
