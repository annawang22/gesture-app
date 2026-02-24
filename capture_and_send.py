"""
Attribution / Use of AI Tools:
The majority of the code in this repository was generated with the assistance of ChatGPT Pro (Feb. 2026).  
I reviewed the generated code, integrated it into this project, tested it locally and on Render, and made edits as needed.
"""

"""
Webcam client:
- Shows live camera feed
- Press 'c' to capture a frame and send to your /predict endpoint
- Press 'q' to quit

Usage:
  python3 capture_and_send.py --url https://gesture-app-restart.onrender.com/predict
"""

import argparse # lets script accept command line arguments (e.g. --url)
import tempfile # for creating temporary files (e.g. to save captured image before sending)
import cv2 # for webcam capture and image processing

# flask - server that waits for requests
# requests - client that makes requests to the server (e.g. to send captured image to our Flask server)
import requests 


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Full /predict URL")
    args = parser.parse_args()

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
            # create a temporary file that ends in .jpg, call it tmp while i'm using it, and automatically delete it when done
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
