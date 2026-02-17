# Gesture Recognizer API (Flask + MediaPipe)

This project is a simple **Flask backend** that runs the **MediaPipe Gesture Recognizer** on an uploaded image and returns the top gesture label + confidence. A small **webcam client script** (`capture_and_send.py`) acts as a “frontend” by capturing frames and calling the backend.

---

## 1) Backend: what it does

### Overview
The backend (`app.py`) loads a MediaPipe **Gesture Recognizer** model (`gesture_recognizer.task`) and exposes HTTP endpoints for:
- health checks
- version info
- gesture prediction from an uploaded image

### Endpoints

#### `GET /`
**Purpose:** Basic “server is up” check (also prevents noisy 404s from probes).  
**Parameters:** none  
**Returns:** plain text
- `200 OK` with body: `OK`

---

#### `GET /healthz`
**Purpose:** Health check used for debugging and monitoring.  
**Parameters:** none  
**Returns:** JSON
- `200 OK`
```json
{"ok": true, "time": 1234567890.123}
```

---

#### `GET /version`
**Purpose:** Confirms which commit/build is currently deployed and which Python version is running.  
**Parameters:** none  
**Returns:** JSON
- `200 OK`
```json
{
  "commit_hint": "v1-debug-2026-02-16-1334",
  "python": "3.12.12 (....)"
}
```

---

#### `POST /predict`
**Purpose:** Run gesture recognition on an uploaded image.  
**Request type:** `multipart/form-data`  
**Required field:**  
- `image` = the uploaded file (JPEG/PNG/etc.)

**Returns (success):** JSON
- `200 OK`
```json
{"label": "Thumb_Up", "score": 0.87}
```

**Returns (client error):**
- `400 Bad Request` if the `image` field is missing or empty:
```json
{"error": "Missing file field 'image'. Send multipart/form-data with image=@file.jpg"}
```

**Returns (server error):**
- `500 Internal Server Error` with a JSON error message and traceback:
```json
{"error": "...", "traceback": "..."}
```

**Notes about backend behavior**
- Images are decoded with **Pillow**, converted to **RGB**, and then **downscaled (max_dim=256)** before inference to reduce memory/time.
- The returned label is the top gesture category from MediaPipe (if nothing is detected, your code may return `"None"` / `0.0` depending on your classifier logic).

---

## 2) “Frontend” (client) and how it talks to the backend

There is no browser UI in this project. Instead, `capture_and_send.py` acts as a lightweight client (“frontend”) that:

1. Opens your webcam using OpenCV (`cv2.VideoCapture(0)`).
2. Displays a live camera window.
3. When you press:
   - **`c`**: captures the current frame, writes it as a temporary `.jpg`, and sends:
     - `POST {URL}/predict`
     - as `multipart/form-data` with `image=@frame.jpg`
   - **`q`**: quits the program
4. Prints the backend response (`label` + `score`) to the terminal.

### Which endpoint it calls
- Calls: `POST /predict`
- Sends: `files = {"image": ("frame.jpg", <bytes>, "image/jpeg")}`
- Uses: `requests.post(..., timeout=90)`
- Displays: status code + response text

---

## 3) Setup and run the backend locally

### Requirements
- Python (your setup commonly uses a `.venv`)
- A MediaPipe task model file:
  - `gesture_recognizer.task` (default expected in the repo root)

### Install dependencies
From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment variables (optional)
The backend supports these env vars:

- `MODEL_PATH`  
  Path to the `.task` model file.  
  Default: `gesture_recognizer.task`

- Optional confidence thresholds:
  - `MIN_HAND_DETECTION_CONF` (default `0.5`)
  - `MIN_HAND_PRESENCE_CONF` (default `0.5`)
  - `MIN_TRACKING_CONF` (default `0.5`)

Example:
```bash
export MODEL_PATH="gesture_recognizer.task"
export MIN_HAND_DETECTION_CONF="0.6"
```

### Run the backend
```bash
source .venv/bin/activate
python app.py
```

Expected output includes something like:
- `Running on http://127.0.0.1:5000`

### Test endpoints locally

Health:
```bash
curl -i http://127.0.0.1:5000/healthz
```

Predict with an image:
```bash
curl -i -X POST "http://127.0.0.1:5000/predict" -F "image=@/FULL/PATH/TO/image.jpg"
```

---

## 4) Run the webcam client (“frontend”) locally

In a **second terminal** (leave the backend running in the first terminal):

```bash
source .venv/bin/activate
python capture_and_send.py --url http://127.0.0.1:5000/predict
```

- Press **`c`** to capture and send a frame
- Press **`q`** to quit

> macOS note: you may need to allow Camera access for Terminal/Python in **System Settings → Privacy & Security → Camera**.

---

## 5) Deploying on Render (backend hosting)

Render runs the backend using `gunicorn`. A working Start Command is:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --worker-class gthread --workers 1 --threads 4 --timeout 600 --graceful-timeout 600 --access-logfile - --error-logfile -
```

Once deployed, you can test:

```bash
curl -i https://YOUR-SERVICE.onrender.com/healthz
curl -i -X POST "https://YOUR-SERVICE.onrender.com/predict" -F "image=@/FULL/PATH/TO/image.jpg"
```

---

## 6) Authentication / secrets handling

This project does **not** use authentication (no API keys, tokens, or user accounts).  
There are **no secrets stored in the client script**.

If you later add secrets (API keys, etc.), the recommended pattern is:
- store secrets as **environment variables** on the backend (Render → Environment)
- **never** hardcode secrets in `capture_and_send.py` or commit them to GitHub
