from ultralytics import YOLO
import cv2
import os

print("⏳ Loading YOLO model locally...")

model = YOLO("best.pt")
print("✅ Model loaded successfully!")

def analyze_image_for_pothole(image_path: str, confidence_threshold=0.5):
    """
    Real AI Model inference using YOLOv8 from Hugging Face.
    Analyzes the image and returns whether a pothole was detected.
    """
    print(f"🧠 AI is analyzing {image_path}...")
    
    
    results = model(image_path, conf=confidence_threshold, verbose=False)
    
    best_confidence = 0.0
    detected = False
    
    for result in results:
        if result.boxes is not None and len(result.boxes) > 0:
            detected = True
           
            for box in result.boxes:
                conf = box.conf[0].item()
                if conf > best_confidence:
                    best_confidence = conf
                    
            
            annotated_frame = result.plot()
            annotated_path = image_path.replace(".", "_annotated.")
            cv2.imwrite(annotated_path, annotated_frame)
            print(f"📸 Saved annotated image to {annotated_path}")
            
    return {
        "detected": detected,
        "confidence": round(best_confidence, 2)
    }
