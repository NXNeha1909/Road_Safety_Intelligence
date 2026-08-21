const startCameraBtn = document.getElementById("startCamera");
const captureBtn = document.getElementById("captureBtn");

const video = document.getElementById("cameraPreview");
const canvas = document.getElementById("canvas");

const status = document.getElementById("cameraStatus");

let stream = null;

// Start Camera

if (startCameraBtn) {
  startCameraBtn.addEventListener("click", async (event) => {
    event.preventDefault();

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
        },

        audio: false,
      });

      video.srcObject = stream;

      status.innerHTML = "🟢 Camera Active";

      console.log("Camera Started");
    } catch (error) {
      console.log("Camera Error:", error);

      alert("Camera permission denied");
    }
  });
}

// Capture + Upload

if (captureBtn) {
  captureBtn.addEventListener("click", (event) => {
    event.preventDefault();

    if (!stream) {
      alert("Start camera first");

      return;
    }

    // Capture frame

    canvas.width = video.videoWidth;

    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    ctx.drawImage(
      video,

      0,

      0,

      canvas.width,

      canvas.height,
    );

    console.log("Image Captured");

    status.innerHTML = "📸 Image Captured";

    // Get Location

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;

        const longitude = position.coords.longitude;

        console.log("Latitude:", latitude);

        console.log("Longitude:", longitude);

        // Convert Image

        canvas.toBlob((blob) => {
          const imageFile = new File(
            [blob],

            "captured-road.jpg",

            {
              type: "image/jpeg",
            },
          );

          console.log("Image File:", imageFile);

          // Form Data

          const formData = new FormData();

          formData.append("image", imageFile);

          formData.append("lat", latitude);

          formData.append("lng", longitude);

          // Backend API Call

          fetch("http://127.0.0.1:8000/report-hazard", {
            method: "POST",

            body: formData,
          })
            .then((response) => response.json())

            .then((data) => {
              console.log("Backend Response:");

              console.log(data);

              if (data.status === "success") {
                status.innerHTML = "⚠️ Pothole Detected";
              } else {
                status.innerHTML = "✅ Road Safe";
              }

              console.log("UI UPDATE DONE");
            })

            .catch((error) => {
              console.log("Backend Error:", error);

              status.innerHTML = "❌ Backend Connection Failed";
            });
        }, "image/jpeg");
      },

      (error) => {
        console.log("Location Error:", error);

        alert("Location permission required");
      },
    );
  });
}
