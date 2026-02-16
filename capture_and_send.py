"""
Webcam client:
- Shows live camera feed
- Press 'c' to capture a frame and send to your /predict endpoint
- Press 'q' to quit

Usage:
  python3 capture_and_send.py --url https://gesture-app-restart.onrender.com/predict
"""

import argparse
import tempfile
# import cv2
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Full /predict URL")
    args = parser.parse_args()

    # health_url = args.url.replace("/predict", "/healthz")
    # print("Warming up:", health_url)
    # try:
    #     r = requests.get(health_url, timeout=60)
    #     print("Warmup status:", r.status_code, r.text[:200])
    # except Exception as e:
    #     print("Warmup error:", e)


    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (VideoCapture(0)).")

    print("Press 'c' to capture+send. Press 'q' to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to read from webcam.")
            continue

        cv2.imshow("webcam (press c to capture+send, q to quit)", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

        if key == ord("c"):
            # Write a temporary JPEG so we can upload it as a file easily
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
                ok = cv2.imwrite(tmp.name, frame)
                if not ok:
                    print("Failed to write temp image.")
                    continue

                with open(tmp.name, "rb") as f:
                    files = {"image": ("frame.jpg", f, "image/jpeg")}
                    try:
                        r = requests.post(args.url, files=files, timeout=90)
                        print("Status:", r.status_code)
                        print("Response:", r.text)
                    except Exception as e:
                        print("Request error:", e)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
