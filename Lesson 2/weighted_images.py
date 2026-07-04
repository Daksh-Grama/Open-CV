"""import cv2
import numpy as np
image1 = cv2.imread("Lesson 2/abstract.jpg")
image2 = cv2.imread("Lesson 2/abstract2.jpg")
print(image1.shape)
print(image2.shape)

image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))



weightedsum = cv2.addWeighted(image1, 0.8, image2, 0.5, 0)
cv2.imshow("Weighted Sum", weightedsum)
cv2.waitKey(0)
cv2.destroyAllWindows()"""

#Subtraction of images

"""import cv2

import numpy as np

image1 = cv2.imread("Lesson 2/abstract.jpg")

image2 = cv2.imread("Lesson 2/abstract2.jpg")

image2 = cv2.resize(image2, (image1.shape[1], image1.shape[0]))

weightedsubtraction = cv2.subtract(image1, image2)

cv2.imshow("Weighted Subtraction", weightedsubtraction)
cv2.waitKey(0)

cv2.destroyAllWindows()"""

#Resizing the image

"""import cv2
image1 = cv2.imread("Lesson 2/abstract.jpg")
cv2.imshow("Original Image", image1)

image1 = cv2.resize(image1, (10000, 10000))
cv2.imshow("Resized Image", image1)

cv2.waitKey(0)
cv2.destroyAllWindows()
"""

#Erode an image

import cv2
import numpy as np

image1 = cv2.imread("Lesson 2/abstract.jpg", 1)

kernel = np.ones((5, 5), np.uint8)

eroded_image = cv2.erode(image1, kernel, iterations=1)

cv2.imshow("Eroded Image", eroded_image)

cv2.waitKey(0)

cv2.destroyAllWindows()