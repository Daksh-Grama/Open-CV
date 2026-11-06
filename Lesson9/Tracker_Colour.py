import cv2
import numpy as np




cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not found!")
    exit()

colors = {
    "Red": [
        ([0, 120, 70], [10, 255, 255]),
        ([170, 120, 70], [180, 255, 255])
    ],
    "Green": [
        ([35, 80, 50], [85, 255, 255])
    ],
    "Blue": [
        ([90, 80, 50], [130, 255, 255])
    ],
    "Yellow": [
        ([20, 100, 100], [35, 255, 255])
    ]
}
while True:
    ret,frame = cap.read()
    if not ret:
        print("Unable to read camera!")
        break
    frame = cv2.flip(frame,1)
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
    for colorname, ranges in colors.items():
        mask = np.zeros(hsv.shape[:2],dtype=np.uint8)
        for lower, upper in ranges:
            lower =  np.array(lower)
            upper = np.array(upper)
            colormask = cv2.inRange(hsv,lower,upper)
            mask = cv2.bitwise_or(mask,colormask)
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask,cv2.MORPH_OPEN,kernel)
        mask = cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel)
        contours, hierarchy = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 800:
                x, y, w, h = cv2.boundingRect(contour)
                centerx = x + w // 2
                centery = y + h // 2
                cv2.rectangle(frame, (x, y), (x + w, y + h), 2)
                cv2.circle(frame, (centerx, centery), 5, -1)
                cv2.putText(frame, colorname, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.imshow("Real Timw Colour Tracker", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()