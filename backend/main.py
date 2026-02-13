import io
import os
from typing import Optional

# converts images into array format MediaPipe can work with
import numpy as np
# Pillow is used to read the uploaded image file and convert it into a format that MediaPipe can process
from PIL import Image as PILImage
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware allows frontend from another origin to call backend

import mediapipe as mp
from mediapipe.tasks.python import vision

app = FastAPI(title="Gesture Label API")

# sets up CORS (cross origin resource sharing) to allow frontend to call backend from a different origin
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the gesture recognizer model at startup
MODEL_PATH = os.getenv("MODEL_PATH", "models/gesture_recognizer.task")
recognizer: Optional[vision.GestureRecognizer] = None

# Loads the gesture recognizer model at application startup. This ensures that the model is ready to use when the first prediction request comes in, reducing latency for the first request. 
import urllib.request

@app.on_event("startup")
def load_model():
    global recognizer
    
    # Download model if not present
    if not os.path.exists("models"):
        os.makedirs("models")
    
    if not os.path.exists(MODEL_PATH):
        print("Downloading gesture recognizer model...")
        url = "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"
        urllib.request.urlretrieve(url, MODEL_PATH)
        print("Model downloaded successfully")
    
    options = vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=vision.RunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    recognizer = vision.GestureRecognizer.create_from_options(options)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/predict")
async def predict(image: UploadFile = File(...)):
    if recognizer is None:
        return {"error": "Model not loaded"}

    data = await image.read()
    pil_img = PILImage.open(io.BytesIO(data)).convert("RGB")
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(pil_img))

    result = recognizer.recognize(mp_image)

    if not result.gestures or not result.gestures[0]:
        return {"label": None, "score": None, "message": "No hand/gesture detected"}

    # Get the top gesture prediction for the first hand detected
    top = result.gestures[0][0]
    return {"label": top.category_name, "score": float(top.score)}
