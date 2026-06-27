"""import cv2

img = cv2.imread("Lesson1\\FalcoMinorKeulemans.jpg", cv2.IMREAD_COLOR)

cv2.imshow("Peregrine Falcon image", img)
cv2.waitKey(0)
cv2.destroyAllWindows()"""



"""import cv2

image = cv2.imread("Lesson1/birdy.jpg", 1)

B, G, R = cv2.split(image)

cv2.imshow("Blue Saturated Image", B)
cv2.waitKey(delay = 5000)

cv2.imshow("Green Saturated Image", G)
cv2.waitKey(delay = 5000)

cv2.imshow("Red Saturated Image", R)
cv2.waitKey(delay = 5000)

cv2.destroyAllWindows()"""
import cv2
import os
image = cv2.imread("Lesson1/birdy.jpg", 1)
image = cv2.imread("Lesson1/birdy.jpg",cv2.IMREAD_GRAYSCALE)
cv2.imshow("Grayscale Image", image)
cv2.imwrite("Lesson1/birdy_gray.jpg", image)
print("Grayscale image saved successfully.")
cv2.waitKey(delay = 5000)
cv2.destroyAllWindows()