"""import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
greyimage = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
cv2.imshow("GrayScale Image", greyimage)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
"""import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
row, col = image2.shape[0:2]
for i in range(row):
    for j in range(col):
        image2[i, j] = sum(image2[i, j])*0.33
cv2.imshow("Grayscale image", image2)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
"""import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
row, col = image2.shape[0:2]
M = cv2.getRotationMatrix2D((col/2, row/2), 90, 1)
Result = cv2.warpAffine(image2, M, (col, row))
cv2.imwrite("Rotation.jpg", Result)
cv2.imshow("Reasult", Result)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
import cv2
import numpy as np
image2 = cv2.imread("Lesson1/FalcoMinorKeulemans.jpg")
cv2.imshow("Original Image", image2)
edges = cv2.Canny(image2, 100, 200)
cv2.imwrite("RR.jpg", edges)
cv2.imshow("Canny image", edges)
cv2.waitKey(0)
cv2.destroyAllWindows()