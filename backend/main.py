import io
import os
from typing import Optional

import numpy as np
from PIL import Image as PILImage
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import mediapipe as mp
from mediapipe.tasks.python import vision

app = FastAPI(title="Gesture Label API")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = os.getenv("MODEL_PATH", "models/gesture_recognizer.task")
recognizer: Optional[vision.GestureRecognizer] = None


@app.on_event("startup")
def load_model():
    global recognizer
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

    top = result.gestures[0][0]
    return {"label": top.category_name, "score": float(top.score)}
