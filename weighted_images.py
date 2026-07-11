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
"""import cv2
import numpy as np
image1 = cv2.imread("Lesson 2/abstract.jpg", 1)
kernel = np.ones((5, 5), np.uint8)
eroded_image = cv2.erode(image1, kernel, iterations=1)
cv2.imshow("Eroded Image", eroded_image)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
#Blurring an image
"""import cv2
import numpy as np
# print("OpenCV version:", cv2.__version__)
# print("NumPy version:", np.__version__)

image2 = cv2.imread("Lesson 2/abstract2.jpg")
cv2.imshow("Original Image", image2)

Gaussian = cv2.GaussianBlur(image2, (7, 7), 0)
cv2.imshow("Gaussian Blur", Gaussian)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
#Median Blur
"""import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
median = cv2.medianBlur(image2, 5)
cv2.imshow("Median Blur", median)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
#Bilateral Blur
"""import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
bilateral = cv2.bilateralFilter(image2, 9, 1000, 1000)
cv2.imshow("Bilateral Blur", bilateral)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
#Bordering an Image
"""import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
bordered = cv2.copyMakeBorder(image2, 0, 0, 10, 10, cv2.BORDER_CONSTANT, value=[45, 63, 77])
cv2.imshow("Bordered Image", bordered)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
bordered = cv2.copyMakeBorder(image2, 10, 10, 10, 10, cv2.BORDER_REFLECT, value=[45, 63, 77])
cv2.imshow("Bordered Image", bordered)
cv2.waitKey(0)
cv2.destroyAllWindows()