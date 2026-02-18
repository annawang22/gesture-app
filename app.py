"""
Attribution / Use of AI Tools:
The majority of the code in this repository was generated with the assistance of ChatGPT Pro (Feb. 2026).  
I reviewed the generated code, integrated it into this project, tested it locally and on Render, and made edits as needed.
"""


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

from werkzeug.exceptions import HTTPException
import concurrent.futures

import psutil


# ----------------------------
# Configuration
# ----------------------------
MODEL_PATH = os.environ.get("MODEL_PATH", "gesture_recognizer.task")

# Optional thresholds (tweak if you get "None" too often)
MIN_HAND_DETECTION_CONF = float(os.environ.get("MIN_HAND_DETECTION_CONF", "0.5"))
MIN_HAND_PRESENCE_CONF = float(os.environ.get("MIN_HAND_PRESENCE_CONF", "0.5"))
MIN_TRACKING_CONF = float(os.environ.get("MIN_TRACKING_CONF", "0.5"))

app = Flask(__name__)

@app.get("/")
def home():
    return "OK", 200

@app.errorhandler(Exception)
def handle_any_exception(e):
    """
    Important: don't convert normal HTTP errors (like 404 Not Found) into 500s.
    Only return 500 JSON for real unexpected exceptions.
    """
    if isinstance(e, HTTPException):
        return e  # keep 404/405/etc as-is

    traceback.print_exc()
    return jsonify({"type": type(e).__name__, "error": str(e)}), 500



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
    - Reads bytes from the request
    - Uses Pillow to decode
    - Returns RGB numpy array (MediaPipe expects SRGB/RGB)
    """
    image_bytes = file_storage.read()
    if not image_bytes:
        raise ValueError("Uploaded file is empty.")

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)

#downscale
def downscale_rgb(rgb, max_dim=512):
    h, w = rgb.shape[:2]
    m = max(h, w)
    if m <= max_dim:
        return rgb
    scale = max_dim / m
    new_w = int(w * scale)
    new_h = int(h * scale)
    # Use OpenCV if you still have it, otherwise Pillow/numpy methods.
    # If you're using Pillow decode already, easiest is:
    img = Image.fromarray(rgb)
    img = img.resize((new_w, new_h))
    return np.array(img)


def recognizer_top_label(rgb_image):
    print("=== recognizer_top_label START ===", flush=True)
    t0 = time.time()

    # Step 1: wrap in mp.Image
    print("Step 1: creating mp.Image...", flush=True)
    rgb_image = np.ascontiguousarray(rgb_image)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
    print(f"Step 1 done: mp.Image created. elapsed={round(time.time()-t0,3)}s", flush=True)

    # Step 2: call recognize()
    print("Step 2: calling recognizer.recognize()...", flush=True)
    t_recognize = time.time()
    result = recognizer.recognize(mp_image)
    print(f"Step 2 done: recognize() returned. elapsed_since_recognize={round(time.time()-t_recognize,3)}s, total_elapsed={round(time.time()-t0,3)}s", flush=True)

    # Step 3: parse result
    print("Step 3: parsing result...", flush=True)
    if result is None or result.gestures is None or len(result.gestures) == 0:
        print("Step 3: no gestures detected. returning None.", flush=True)
        return "None", 0.0

    first_hand = result.gestures[0]
    if not first_hand:
        print("Step 3: first_hand is empty. returning None.", flush=True)
        return "None", 0.0

    top_category = first_hand[0]
    label = getattr(top_category, "category_name", None) or "None"
    score = float(getattr(top_category, "score", 0.0) or 0.0)
    print(f"Step 3 done: label={label}, score={score}. total_elapsed={round(time.time()-t0,3)}s", flush=True)

    print("=== recognizer_top_label END ===", flush=True)
    return label, score

# ----------------------------
# Routes
# ----------------------------


@app.get("/healthz")
def healthz():
    mem = psutil.virtual_memory()
    return jsonify({
        "ok": True,
        "time": time.time(),
        "mem_used_mb": mem.used / 1024**2,
        "mem_available_mb": mem.available / 1024**2,
    }), 200


@app.post("/predict")
def predict():
    """
    Expects: multipart/form-data with a file field named "image".
    Returns: JSON { label, score }

    Debugging goal:
    - Print timestamps after each major step so we can see where it hangs on Render.
    """
    print("HIT /predict", flush=True)
    t0 = time.time()  # start timer for this request

    try:
        # 1) Validate request format
        if "image" not in request.files:
            print("missing 'image' field", flush=True)
            return jsonify({
                "error": "Missing file field 'image'. Send multipart/form-data with image=@file.jpg"
            }), 400

        file = request.files["image"]
        if not file or file.filename == "":
            print("empty filename / no file selected", flush=True)
            return jsonify({"error": "No file selected."}), 400

        print(f"got file: name={file.filename}", "elapsed:", round(time.time() - t0, 3), flush=True)

        # 2) Decode bytes -> RGB numpy array
        rgb = decode_image_from_request(file)
        print("decoded rgb shape:", getattr(rgb, "shape", None),
              "elapsed:", round(time.time() - t0, 3), flush=True)

        # 3) Downscale to reduce memory/time
        rgb = downscale_rgb(rgb, max_dim=256)
        print("downscaled shape:", getattr(rgb, "shape", None),
              "elapsed:", round(time.time() - t0, 3), flush=True)

        # 4) Run MediaPipe recognizer
        label, score = recognizer_top_label(rgb)
        print("recognizer done",
              "elapsed:", round(time.time() - t0, 3), flush=True)

        return jsonify({"label": label, "score": score}), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc(),
        }), 500



# Local dev entrypoint (Render will use gunicorn instead)
if __name__ == "__main__":
    # For local testing: python app.py
    app.run(host="0.0.0.0", port=5000, debug=True)
