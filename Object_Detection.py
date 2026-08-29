import cv2
import numpy as np
image2 = cv2.imread("Lesson5/gettyimages-dv180010a-612x612.jpg")
cv2.imshow("Original Image", image2)

grey = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
greyblur = cv2.blur(grey, (3,3))
cv2.imshow("Grey Blurred Image", greyblur)
detected_circles = cv2.HoughCircles(greyblur, cv2.HOUGH_GRADIENT, 1, 20, param1 = 50, param2 = 50, minRadius = 1, maxRadius = 40)


if detected_circles is not None:
    detected_circles = np.uint16(np.around(detected_circles))
    for pt in detected_circles[0, :]:
        a, b, r = pt[0], pt[1], pt[2]
        cv2.circle(image2, (a, b), r, (0, 255, 0), 2)
        cv2.imshow("Detected Circles", image2)
        cv2.waitKey(0)
cv2.destroyAllWindows()