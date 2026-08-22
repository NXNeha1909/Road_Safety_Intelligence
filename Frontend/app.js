const startCameraBtn = document.getElementById("startCamera");
const captureBtn = document.getElementById("captureBtn");

const video = document.getElementById("cameraPreview");
const canvas = document.getElementById("canvas");

const status = document.getElementById("cameraStatus");

let stream = null;

// START CAMERA

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

      await video.play();

      status.innerHTML = "🟢 Camera Active";

      console.log("Camera Started");
    } catch (error) {
      console.log("Camera Error:", error);

      alert("Camera permission denied");
    }
  });
}

// CAPTURE IMAGE

if (captureBtn) {
  captureBtn.addEventListener("click", async (event) => {
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

    // Location

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const latitude = position.coords.latitude;

        const longitude = position.coords.longitude;

        console.log("Latitude:", latitude);

        console.log("Longitude:", longitude);

        // Convert canvas to image

        canvas.toBlob(
          async (blob) => {
            const imageFile = new File(
              [blob],

              "captured-road.jpg",

              {
                type: "image/jpeg",
              },
            );

            console.log("Image File:", imageFile);

            const formData = new FormData();

            formData.append("image", imageFile);

            formData.append("lat", latitude);

            formData.append("lng", longitude);

            try {
              const response = await fetch(
                "http://127.0.0.1:8000/report-hazard",
                {
                  method: "POST",

                  body: formData,
                },
              );

              const data = await response.json();

              console.log("Backend Response:");
              video.srcObject = stream;
              console.log(data);

              if (data.status === "success") {
                status.innerHTML = "⚠️ Pothole Detected";
                console.log("Camera still running");
              } else {
                status.innerHTML = "✅ Road Safe";
              }
            } catch (error) {
              console.log("Backend Error:", error);

              status.innerHTML = "❌ Backend Error";
            }

            // IMPORTANT
            // Keep camera alive

            video.srcObject = stream;
          },

          "image/jpeg",
        );
      },

      (error) => {
        console.log("Location Error:", error);

        alert("Location permission required");
      },
    );
  });
}
