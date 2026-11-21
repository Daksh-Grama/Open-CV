import cv2
import numpy as np
import time
from datetime import datetime
from pathlib import Path

sec = cv2.VideoCapture(0)
if not sec.isOpened():
    print("Camera is not found!")
else:
    bg = cv2.createBackgroundSubtractorMOG2(
        history=500,
        varThreshold=50,
        detectShadows=True,
    )
    kernel = np.ones((5, 5), np.uint8)
    last_alert_time = 0
    alert_interval = 2
    last_photo_time = 0
    photo_interval = 10
    minimum_motion_area = 1000
    photos_directory = Path(__file__).resolve().parent / "motion_captures"
    photos_directory.mkdir(exist_ok=True)

    print("Motion Detection has Started.")
    print("Waiting for Movement...")

    try:
        while True:
            ret, frame = sec.read()
            if not ret:
                print("Failed to capture frame from camera. Exiting...")
                break

            frame = cv2.flip(frame, 1)
            mask = bg.apply(frame)

            # Remove gray shadow pixels and small noise.
            _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            contours, _ = cv2.findContours(
                mask,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE,
            )

            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) < minimum_motion_area:
                    continue

                motion_detected = True
                x, y, width, height = cv2.boundingRect(contour)
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2,
                )

            if motion_detected:
                current_time = time.time()
                if current_time - last_alert_time >= alert_interval:
                    detected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    print(f"Motion detected at {detected_at}")
                    last_alert_time = current_time

                if current_time - last_photo_time >= photo_interval:
                    photo_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    photo_path = photos_directory / f"motion_{photo_timestamp}.jpg"
                    if cv2.imwrite(str(photo_path), frame):
                        print(f"Motion photo saved: {photo_path}")
                        last_photo_time = current_time
                    else:
                        print(f"Failed to save motion photo: {photo_path}")

            cv2.imshow("Security Camera", frame)
            cv2.imshow("Motion Mask", mask)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or key == 27:
                break
    finally:
        sec.release()
        cv2.destroyAllWindows()
    