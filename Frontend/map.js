const hazardIcon = L.icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/564/564619.png",

  iconSize: [40, 40],
});

// Create Map

const map = L.map("map").setView(
  [28.6139, 77.209],

  12,
);

// Store hazard locations

const hazardPoints = [];

// Add OpenStreetMap Layer

L.tileLayer(
  "https://tile.openstreetmap.org/{z}/{x}/{y}.png",

  {
    attribution: "© OpenStreetMap contributors",
  },
).addTo(map);

// Fetch Hazards

fetch("http://127.0.0.1:8000/hazards")
  .then((response) => response.json())

  .then((result) => {
    const countBox = document.getElementById("hazardCount");

    if (countBox) {
      countBox.innerHTML = `⚠️ Hazards Detected: ${result.total}`;
    }
    console.log("Hazard Data:", result);

    result.data.forEach((hazard) => {
      // Skip invalid coordinates

      if (hazard.latitude === 0 || hazard.longitude === 0) {
        return;
      }

      // Save coordinates for zoom

      hazardPoints.push([hazard.latitude, hazard.longitude]);

      // Create Marker

      const marker = L.marker(
        [hazard.latitude, hazard.longitude],

        {
          icon: hazardIcon,
        },
      ).addTo(map);

      // Popup Content

      marker.bindPopup(`


            <div>


            <h3>
            ⚠️ Pothole Detected
            </h3>


            <p>

            Confidence:

            ${(hazard.confidence * 100).toFixed(1)}%

            </p>



            <p>

            Time:

            ${hazard.timestamp}

            </p>


            </div>


        `);
    });

    // Auto Zoom

    if (hazardPoints.length > 0) {
      map.fitBounds(hazardPoints);
    }
  })

  .catch((error) => {
    console.log(
      "Hazard Fetch Error:",

      error,
    );
  });

console.log("Map Loaded");
