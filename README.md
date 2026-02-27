# Gesture-Controlled Spotify App

Control Spotify playback using hand gestures captured through your webcam — no keyboard required.

🔗 **Live site:** [https://annawang22.github.io/gesture-app/](https://annawang22.github.io/gesture-app/)

---

## What It Does

This app lets you control Spotify using hand gestures detected by your webcam. You open the site in your browser, connect your Spotify account, start your camera, and hold up a hand gesture. The app captures a frame, sends it to a Flask backend running on Render, which uses Google's MediaPipe to identify the gesture and return a label. The frontend then calls the Spotify API to carry out the corresponding action.

| Gesture | Action |
|---|---|
| ☝️ Pointing finger up | Skip to next track |
| ✊ Closed fist | Pause |
| 🖐 Open palm | Play / Resume |

---

## How to Use It

1. Visit the [live site](https://annawang22.github.io/gesture-app/)
2. Click **Connect Spotify** and log in with your Spotify account
3. Make sure Spotify is actively playing on one of your devices
4. Click **Start Camera** and allow webcam access
5. Hold up a hand gesture and click **Capture & Predict**
6. The detected gesture label and confidence score will appear, and your music will respond

> **Note:** The app is in Spotify's Development Mode. Unfortunately, if you are not the app owner, you need to be added as a user in the Spotify Developer Dashboard before you can connect. Contact the app owner through this [Google Form](https://forms.gle/Qz86m32RgHH5DZ1o6) to be added.

---

## Features I'm Most Proud Of

**End-to-end gesture-to-music pipeline** — Intertwining the browser webcam frontend, a Flask REST API backend hosted on Render, a MediaPipe machine learning model, and the Spotify Web API to work seamlessly

**Spotify PKCE authentication** — The app uses Spotify's modern PKCE authorization flow, which is designed for frontend applications and works without a client secret. I learned how OAuth redirects work, debugged multiple authentication errors (invalid redirect URIs, deprecated response types), and got the login flow working end to end.

**UI/UX Design** — I'm really proud of how the interface came out, from the overall dark theme and color choices down to the smaller details like the animated scan line during capture, the flash effect, and the way gesture results are displayed with a confidence bar and color-coded status indicator.

---

## How to Run It Locally

### Requirements
- Python 3.9+
- A Spotify Premium account
- A Spotify Developer app with `http://127.0.0.1:8888/callback` added as a Redirect URI

### Backend

```bash
git clone https://github.com/annawang22/gesture-app.git
cd gesture-app
pip install -r requirements.txt
python3 app.py
```

The backend runs at `http://localhost:5000`.

### Frontend

```bash
python3 server.py
```

Then visit `http://127.0.0.1:8888` in your browser.

> The frontend must be served over HTTP (not opened as a file) for the Spotify auth redirect to work. `server.py` handles this and also intercepts the Spotify callback redirect correctly.

---

## How Secrets Are Handled

This project uses Spotify's **PKCE Authorization Flow**, which is designed for frontend applications and does not require a client secret. The only credential stored in the codebase is the **Spotify Client ID**, which is intentionally public — it is visible in the browser's Network tab during any login flow and poses no security risk on its own.

---

## Project Structure

```
gesture-app/
├── app.py                   # Flask backend — gesture recognition API
├── capture_and_send.py      # Legacy CLI client (replaced by index.html)
├── index.html               # Browser frontend — webcam + Spotify integration
├── server.py                # Local dev server with Spotify callback handling
├── spotify_config.js        # Spotify Client ID and Redirect URI
├── gesture_recognizer.task  # Pre-trained MediaPipe gesture model
├── requirements.txt         # Python dependencies
└── .gitignore
```

---

## Tech Stack

- **Backend:** Python, Flask, MediaPipe, Pillow, NumPy, psutil, flask-cors, Gunicorn
- **Frontend:** HTML, CSS, Vanilla JavaScript, Spotify Web API, PKCE Auth Flow
- **Hosting:** Render (backend), GitHub Pages (frontend)

---

## Attribution

Parts of the code in this repository was generated with the assistance of ChatGPT Pro and Claude (Feb. 2026). Code was reviewed, integrated, tested locally and on Render, and edited as needed.

The gesture recognition model (`gesture_recognizer.task`) is provided by Google via the [MediaPipe](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer) library.
