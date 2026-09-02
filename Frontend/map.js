const API_BASE = "http://127.0.0.1:8000";

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
const hazardMarkers = {}; // id -> L.marker, so we can remove one after it's resolved

// Map Layer

L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

// Load Hazards

function hazardPopupHtml(hazard) {
  const typeLabel = (hazard.hazard_type || "pothole").replace("_", " ");
  return `
      <div>
        <h3>⚠️ ${typeLabel.charAt(0).toUpperCase() + typeLabel.slice(1)}</h3>
        <p>Confidence: ${(hazard.confidence * 100).toFixed(1)}%</p>
        <p>Observed: ${hazard.observation_count || 1} time(s)</p>
        <p>Last update: ${hazard.timestamp ? new Date(hazard.timestamp).toLocaleString() : "--"}</p>
        <div class="hazard-popup-actions">
          <button class="hazard-fixed-btn" data-id="${hazard.id}" data-action="fixed">This is fixed</button>
          <button class="hazard-wrong-btn" data-id="${hazard.id}" data-action="wrong">Wrong report</button>
        </div>
      </div>
    `;
}

function resolveHazard(id, action, marker) {
  const formData = new FormData();
  formData.append("action", action);

  fetch(`${API_BASE}/resolve-hazard/${id}`, {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "success") {
        map.removeLayer(marker);
        delete hazardMarkers[id];

        const countBox = document.getElementById("hazardCount");
        const remaining = Object.keys(hazardMarkers).length;
        if (countBox) {
          countBox.innerHTML = `⚠️ Hazards Detected: ${remaining}`;
        }
      } else {
        alert(data.message || "Could not update this hazard right now.");
      }
    })
    .catch((error) => {
      console.log(error);
      alert("Could not reach the server. Please try again.");
    });
}

function loadHazards() {
  const countBox = document.getElementById("hazardCount");

  fetch(`${API_BASE}/hazards`)
    .then((response) => response.json())
    .then((result) => {
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

        marker.bindPopup(hazardPopupHtml(hazard));

        marker.on("popupopen", () => {
          const popupEl = marker.getPopup().getElement();
          popupEl.querySelectorAll(".hazard-popup-actions button").forEach((btn) => {
            btn.addEventListener("click", () => {
              resolveHazard(hazard.id, btn.dataset.action, marker);
            });
          });
        });

        hazardMarkers[hazard.id] = marker;
      });

      if (hazardPoints.length > 0) {
        map.fitBounds(hazardPoints);
      }
    })
    .catch((error) => {
      console.log("Hazard Fetch Error:", error);
      if (countBox) {
        countBox.innerHTML = "⚠️ Couldn't load hazards — check the server connection";
      }
    });
}

loadHazards();

// User Location
let userMarker = null;
let globalUserLat = 0;
let globalUserLng = 0;

function updateUserLocation(position) {
  const lat = position.coords.latitude;
  const lng = position.coords.longitude;
  globalUserLat = lat;
  globalUserLng = lng;

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

// Point 1: Custom Destination + Route Logic (Hiding Default UI)
let routingControl = null;
let routeReady = false;

const startNavBtn = document.getElementById("startNavBtn");

// Recenter Button Logic
document.getElementById('recenterBtn').addEventListener('click', () => {
    if (globalUserLat !== 0) {
        map.setView([globalUserLat, globalUserLng], 15);
    } else {
        alert("Waiting for your GPS location...");
    }
});

// Custom Search Box Logic
const routeBtn = document.getElementById('routeBtn');

routeBtn.addEventListener('click', () => {
    const dest = document.getElementById('destInput').value;

    if (!dest) {
        return alert("Please enter a destination!");
    }
    if (globalUserLat === 0) {
        return alert("Waiting for your GPS location...");
    }

    const originalLabel = routeBtn.innerHTML;
    routeBtn.disabled = true;
    routeBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Searching...`;

    // 1. Fetch Coordinates for the entered city/place using Nominatim API
    fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(dest)}`)
    .then(res => res.json())
    .then(data => {
        if (data.length === 0) {
            return alert("Location not found! Try a different name.");
        }

        const destLat = data[0].lat;
        const destLng = data[0].lon;

        if (routingControl) {
            map.removeControl(routingControl);
        }

        // 2. Draw Route but HIDE the white box (show: false)
        routingControl = L.Routing.control({
            waypoints: [
                L.latLng(globalUserLat, globalUserLng),
                L.latLng(destLat, destLng)
            ],
            show: false, // THIS HIDES THE CLUNKY WHITE BOX
            addWaypoints: false,
            routeWhileDragging: false,
            lineOptions: {
                styles: [{color: '#2196F3', opacity: 0.8, weight: 6}]
            },
            createMarker: function(i, wp, nWps) {
                if (i === nWps - 1) {
                    // Only show a marker at the final destination
                    return L.marker(wp.latLng).bindPopup("📍 Destination: " + dest);
                }
                return null;
            }
        }).addTo(map);

        // 3. Zoom map to fit the entire route
        const bounds = new L.featureGroup([
            L.marker([globalUserLat, globalUserLng]),
            L.marker([destLat, destLng])
        ]);
        map.fitBounds(bounds.getBounds(), {padding: [50, 50]});

        routeReady = true;
        if (startNavBtn) startNavBtn.disabled = false;
    })
    .catch(err => {
        console.log(err);
        alert("Error finding route.");
    })
    .finally(() => {
        routeBtn.disabled = false;
        routeBtn.innerHTML = originalLabel;
    });
});

// ================= NAVIGATE ONLY MODE (Task 3) =================
// Camera stays off entirely in this mode. We just watch GPS and poll
// the existing /check-warning endpoint for hazards near the user.

const stopNavBtn = document.getElementById("stopNavBtn");
const navModeStatus = document.getElementById("navModeStatus");
const navModeLabel = document.getElementById("navModeLabel");
const navModeHint = document.getElementById("navModeHint");
const navWarningBanner = document.getElementById("navWarningBanner");
const navWarningMessage = document.getElementById("navWarningMessage");
const dismissNavWarning = document.getElementById("dismissNavWarning");

let navProximityTimer = null;
let navWarningTimer = null;
let lastNavVoiceTime = 0;

function navVoiceAlert(message) {
  if (!("speechSynthesis" in window)) return;

  const now = Date.now();
  if (now - lastNavVoiceTime < 8000) return;
  lastNavVoiceTime = now;

  speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(message);
  speech.lang = "en-US";
  speech.rate = 1;
  speechSynthesis.speak(speech);
}

function showNavWarning(message) {
  navWarningMessage.textContent = message;
  navWarningBanner.hidden = false;

  requestAnimationFrame(() => {
    navWarningBanner.classList.add("show");
  });

  navVoiceAlert("Warning. Hazard detected ahead. Please slow down.");

  clearTimeout(navWarningTimer);
  navWarningTimer = setTimeout(hideNavWarning, 6000);
}

function hideNavWarning() {
  navWarningBanner.classList.remove("show");
  setTimeout(() => {
    navWarningBanner.hidden = true;
  }, 450);
}

dismissNavWarning?.addEventListener("click", () => {
  clearTimeout(navWarningTimer);
  hideNavWarning();
});

startNavBtn?.addEventListener("click", () => {
  if (!routeReady) {
    alert("Search a route first.");
    return;
  }

  startNavBtn.hidden = true;
  stopNavBtn.hidden = false;
  navModeStatus.classList.add("active");
  navModeLabel.textContent = "Navigate Only Mode: On (camera off)";
  navModeHint.textContent = "Watching your route for hazards. Camera is not being used in this mode.";

  navProximityTimer = setInterval(() => {
    if (globalUserLat === 0) return;

    fetch(`${API_BASE}/check-warning?lat=${globalUserLat}&lng=${globalUserLng}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.warning) {
          showNavWarning(data.message || "Hazard reported near your route. Please slow down.");
        }
      })
      .catch((error) => console.log(error));
  }, 4000);
});

stopNavBtn?.addEventListener("click", () => {
  clearInterval(navProximityTimer);
  navProximityTimer = null;

  startNavBtn.hidden = false;
  stopNavBtn.hidden = true;
  navModeStatus.classList.remove("active");
  navModeLabel.textContent = "Navigate Only Mode: Off";
  navModeHint.textContent = "Search a route first, then start navigation to get hazard warnings without using your camera.";

  hideNavWarning();
});

// Auto-hint when arriving via the "Navigate Without Camera" link from the
// detection page, so the user knows what to do next.
if (new URLSearchParams(window.location.search).get("mode") === "navigate") {
  navModeHint.textContent = "Enter a destination and search a route to begin navigating without your camera.";
}
