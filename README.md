# AI-Powered Pothole Finder (Backend)

This is the FastAPI backend for the Road Safety Hackathon project. It receives images, analyzes them for potholes using an AI model, and stores the coordinates in a SQLite database.

## 🚀 How to Run the Server

1. Open your terminal in this folder.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
4. Open the Interactive API Docs (Swagger UI) in your browser:
   👉 **http://127.0.0.1:8000/docs**

---

## 🔌 API Endpoints (For Frontend Developer)

### 1. Upload & Analyze Image
* **URL**: `POST /report-hazard`
* **Content-Type**: `multipart/form-data`
* **Body Parameters**:
  * `lat` (float): Latitude of the device
  * `lng` (float): Longitude of the device
  * `image` (file): The photo captured by the user
* **Response**: Returns JSON indicating if a pothole was detected and its confidence score.

### 2. Get All Hazards for Map
* **URL**: `GET /hazards`
* **Response**: Returns a JSON array of all detected potholes with their `latitude`, `longitude`, `confidence`, and `image_path`. Use this to plot red markers on Leaflet.js map.
