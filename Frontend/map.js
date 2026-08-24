const hazardIcon = L.icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/564/564619.png",

  iconSize: [40, 40],
});

const userIcon = L.divIcon({
  className: "user-location-marker",

  html: '<div class="user-location-dot"><div class="pulse"></div><div class="core"></div></div>',

  iconSize: [16, 16],

  iconAnchor: [8, 8],
});

// Create Map

const map = L.map("map").setView([28.6139, 77.209], 12);

const hazardPoints = [];

// Map Layer

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

// Load Hazards

fetch("http://127.0.0.1:8000/hazards")
  .then((response) => response.json())

  .then((result) => {
    const countBox = document.getElementById("hazardCount");

    if (countBox) {
      countBox.innerHTML = `⚠️ Hazards Detected: ${result.total}`;
    }

    console.log("Hazard Data:", result);

    result.data.forEach((hazard) => {
      if (hazard.latitude === 0 || hazard.longitude === 0) {
        return;
      }

      hazardPoints.push([hazard.latitude, hazard.longitude]);

      const marker = L.marker([hazard.latitude, hazard.longitude], {
        icon: hazardIcon,
      }).addTo(map);

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

    if (hazardPoints.length > 0) {
      map.fitBounds(hazardPoints);
    }
  })

  .catch((error) => {
    console.log("Hazard Fetch Error:", error);
  });

// User Location

let userMarker = null;

function updateUserLocation(position) {
  const lat = position.coords.latitude;

  const lng = position.coords.longitude;

  if (!userMarker) {
    userMarker = L.marker([lat, lng], {
      icon: userIcon,
      zIndexOffset: 1000,
    })
      .addTo(map)
      .bindPopup("🔵 Your Location");

    console.log("User Location:", lat, lng);
  } else {
    userMarker.setLatLng([lat, lng]);
  }
}

function locationError(error) {
  console.log("Location Error:", error);
}

if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    updateUserLocation,

    locationError,

    {
      enableHighAccuracy: true,
      timeout: 8000,
    },
  );

  navigator.geolocation.watchPosition(
    updateUserLocation,

    locationError,

    {
      enableHighAccuracy: true,
      maximumAge: 5000,
      timeout: 8000,
    },
  );
} else {
  console.log("Geolocation not supported");
}

console.log("Map Loaded");
