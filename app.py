"""
Flask + MediaPipe Gesture Recognizer (IMAGE mode)

Endpoints:
  GET  /healthz   -> quick health check
  POST /predict   -> multipart/form-data with file field "image"
                    returns JSON with top gesture label + confidence

Render tips:
  - Use gunicorn start command (see below)
  - Set env var MODEL_PATH if your model isn't in the repo root
"""

import os
import time
import traceback

from PIL import Image
import io
import numpy as np

from flask import Flask, request, jsonify

import mediapipe as mp


# ----------------------------
# Configuration
# ----------------------------
MODEL_PATH = os.environ.get("MODEL_PATH", "gesture_recognizer.task")

# Optional thresholds (tweak if you get "None" too often)
MIN_HAND_DETECTION_CONF = float(os.environ.get("MIN_HAND_DETECTION_CONF", "0.5"))
MIN_HAND_PRESENCE_CONF = float(os.environ.get("MIN_HAND_PRESENCE_CONF", "0.5"))
MIN_TRACKING_CONF = float(os.environ.get("MIN_TRACKING_CONF", "0.5"))

app = Flask(__name__)

@app.errorhandler(Exception)
def handle_exception(e):
    traceback.print_exc()  # shows full traceback in Render logs
    return jsonify({
        "type": type(e).__name__,
        "error": str(e),
    }), 500



@app.get("/version")
def version():
    return {
        "commit_hint": "v1-debug-2026-02-16-1334",
        "python": os.sys.version,
    }, 200


# ----------------------------
# MediaPipe recognizer setup
# ----------------------------
# Following the official MediaPipe Tasks Python pattern:
# BaseOptions + GestureRecognizerOptions + RunningMode.IMAGE + create_from_options()
# :contentReference[oaicite:3]{index=3}
BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


def build_recognizer():
    """
    Create and return a GestureRecognizer instance.
    We keep one global instance (fast) instead of reloading the model per request (slow).
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at '{MODEL_PATH}'. "
            "Download a gesture_recognizer.task model and put it there, "
            "or set MODEL_PATH env var."
        )

    options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=MODEL_PATH),
        running_mode=VisionRunningMode.IMAGE,
        num_hands=1,
        min_hand_detection_confidence=MIN_HAND_DETECTION_CONF,
        min_hand_presence_confidence=MIN_HAND_PRESENCE_CONF,
        min_tracking_confidence=MIN_TRACKING_CONF,
    )
    return GestureRecognizer.create_from_options(options)


# Create the recognizer once at startup so requests are fast.
# If this fails, the service should crash early with a clear error.
recognizer = build_recognizer()


# ----------------------------
# Helpers
# ----------------------------
def decode_image_from_request(file_storage):
    """
    Convert an uploaded image (werkzeug FileStorage) into an RGB numpy array.
    - Reads bytes
    - cv2.imdecode -> BGR
    - convert to RGB (MediaPipe expects SRGB)
    """
    image_bytes = file_storage.read()
    if not image_bytes:
        raise ValueError("Uploaded file is empty.")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)


def recognizer_top_label(rgb_image):
    """
    Run gesture recognition and return (label, score).
    If nothing is detected, return ("None", 0.0).

    Result structure (high level):
      result.gestures -> list (per hand) of lists of Categories
      each Category has category_name + score
    """
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    # IMAGE mode uses recognize(...) and blocks until done. :contentReference[oaicite:4]{index=4}
    result = recognizer.recognize(mp_image)

    # Defensive parsing with lots of checks for "no hands" cases:
    if result is None or result.gestures is None or len(result.gestures) == 0:
        return "None", 0.0

    first_hand = result.gestures[0]
    if first_hand is None or len(first_hand) == 0:
        return "None", 0.0

    top_category = first_hand[0]
    label = getattr(top_category, "category_name", None) or "None"
    score = float(getattr(top_category, "score", 0.0) or 0.0)

    return label, score


# ----------------------------
# Routes
# ----------------------------
@app.get("/healthz")
def healthz():
    return jsonify({"ok": True, "time": time.time()}), 200


@app.post("/predict")
def predict():
    """
    Expects: multipart/form-data with a file field named "image".
    Returns: JSON { label, score }
    """
    try:
        if "image" not in request.files:
            return jsonify({
                "error": "Missing file field 'image'. Send multipart/form-data with image=@file.jpg"
            }), 400

        file = request.files["image"]
        if not file or file.filename == "":
            return jsonify({"error": "No file selected."}), 400

        rgb = decode_image_from_request(file)
        label, score = recognizer_top_label(rgb)

        return jsonify({
            "label": label,
            "score": score,
        }), 200

    except Exception as e:
        # Print full traceback to logs (Render logs will show this)
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500


# Local dev entrypoint (Render will use gunicorn instead)
if __name__ == "__main__":
    # For local testing: python app.py
    app.run(host="0.0.0.0", port=5000, debug=True)
