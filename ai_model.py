import os
import json
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
    print("✅ Gemini API configured.")
else:
    print("⚠️ WARNING: GEMINI_API_KEY not found in .env file!")

# Using gemini-1.5-flash which is extremely fast and multimodal
# (Note: Google doesn't have 3.5-flash-lite, gemini-1.5-flash is the correct one)
generation_config = {
  "temperature": 0.1, # Low temp for consistent JSON output
  "response_mime_type": "application/json",
}

# Initialize the model
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash-lite",
    generation_config=generation_config
)

def analyze_image_for_pothole(image_path: str, confidence_threshold=0.5):
    """
    Real AI Model inference using Google Gemini Vision API.
    Analyzes the image and returns whether a pothole was detected.
    """
    print(f"🤖 Gemini AI is analyzing {image_path}...")
    
    try:
        # Load image for Gemini
        img = Image.open(image_path)
        
        # Prompt forces a strict JSON structure
        prompt = """
        You are a Road Safety AI. Analyze this image for road hazards, specifically potholes.
        Return ONLY a JSON object with two keys:
        - "detected": boolean (true if a clear pothole or severe road damage is visible, false otherwise)
        - "confidence": float between 0.0 and 1.0 representing how sure you are.
        
        JSON format exactly like this:
        {"detected": true, "confidence": 0.85}
        """
        
        response = model.generate_content([prompt, img])
        
        # Parse the JSON response
        result_text = response.text.strip()
        result_json = json.loads(result_text)
        
        detected = bool(result_json.get("detected", False))
        confidence = float(result_json.get("confidence", 0.0))
        
        # Only accept if confidence is above the threshold (acting like YOLO)
        if confidence < confidence_threshold:
            detected = False
            
        print(f"✅ Gemini Response: Detected={detected}, Confidence={confidence}")
        
        return {
            "detected": detected,
            "confidence": round(confidence, 2)
        }
        
    except Exception as e:
        print(f"❌ Error during Gemini API call: {e}")
        return {
            "detected": False,
            "confidence": 0.0
        }
