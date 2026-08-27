# 🎨 Frontend Developer Guide

Hello Frontend Master! 👋 
The backend is completely ready. Your job is to build the UI and connect to these 3 APIs. 

**Base URL:** `http://127.0.0.1:8000`

---

### 1. Upload Image (Camera/Dashcam)
This API sends an image and GPS coordinates to the AI for analysis.

**Endpoint:** `POST /report-hazard`

**JavaScript/React Example:**
```javascript
async function uploadHazard(file, lat, lng) {
    const formData = new FormData();
    formData.append("lat", lat);
    formData.append("lng", lng);
    formData.append("image", file); // The image file from <input type="file">

    try {
        const response = await fetch("http://127.0.0.1:8000/report-hazard", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        console.log("Upload Result:", data);
        // data.status will be "success" if a pothole is found.
    } catch (error) {
        console.error("Error:", error);
    }
}
```

---

### 2. Show Markers on the Map (Dashboard)
This API gives you all the saved potholes. You need to map through them and drop Red Markers (⚠️) on your Leaflet.js/Google Map.

**Endpoint:** `GET /hazards`

**JavaScript/React Example:**
```javascript
async function loadMapData() {
    try {
        const response = await fetch("http://127.0.0.1:8000/hazards");
        const result = await response.json();
        
        console.log("Total Hazards:", result.total);
        
        // Loop through the data to put pins on the map
        result.data.forEach(pothole => {
            console.log(`Pothole at ${pothole.latitude}, ${pothole.longitude} with Confidence: ${pothole.confidence}`);
            // TODO: Add Leaflet marker logic here
        });
    } catch (error) {
        console.error("Error:", error);
    }
}
```

---

### 3. Live Driving Warning (Proximity Alert)
Use `setInterval` to call this API every 3-5 seconds while the user is "Driving". It checks if a pothole is within 200 meters of their current GPS location.

**Endpoint:** `GET /check-warning?lat=YOUR_LAT&lng=YOUR_LNG`

**JavaScript/React Example:**
```javascript
async function checkLiveWarning(currentLat, currentLng) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/check-warning?lat=${currentLat}&lng=${currentLng}`);
        const data = await response.json();
        
        if (data.warning === true) {
            // TODO: Show RED BANNER on screen and play a BEEP SOUND!
            alert(data.message); // Example: "⚠️ ALERT! 1 pothole(s) detected within 200m ahead."
        }
    } catch (error) {
        console.error("Error:", error);
    }
}

// Run this every 5 seconds using HTML5 Geolocation
// setInterval(() => { get_location_and_call_checkLiveWarning() }, 5000);
```


