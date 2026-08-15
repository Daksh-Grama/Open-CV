"""import cv2
import numpy as np
image2 = cv2.imread("Lesson 2/abstract.jpg")
cv2.imshow("Original Image", image2)
start = (0,0)
end = (1300,1300)
color = (100, 100, 100)
thickness = (100)
Line = cv2.line(image2, start, end, color, thickness)
cv2.imshow("Image with a Line on It", Line)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
"""import cv2
import numpy as np
image2 = cv2.imread("Lesson 2/abstract.jpg")
cv2.imshow("Original Image", image2)
start = (0,0)
end = (1300,1300)
color = (100, 50, 200)
thickness = (-1)
Line = cv2.rectangle(image2, start, end, color, thickness)
cv2.imshow("Image with a Rectangle on It", Line)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
"""import cv2
import numpy as np
image2 = cv2.imread("Lesson 2/abstract.jpg")
cv2.imshow("Original Image", image2)
start = (650, 650)
end = (200)
color = (255, 50, 200)
thickness = (-1)
Line = cv2.circle(image2, start, end, color, thickness)
cv2.imshow("Image with a Circle on It", Line)
cv2.waitKey(0)
cv2.destroyAllWindows()"""
import cv2
import numpy as np
image2 = cv2.imread("Lesson 2/abstract.jpg")
cv2.imshow("Original Image", image2)
position = (450, 650)
color = (255, 50, 200)
FontScale = (7)
thickness = (1000)
Font = cv2.FONT_HERSHEY_COMPLEX
Line = cv2.putText(image2, "Hello", position, Font, FontScale, color, thickness, cv2.LINE_AA)
cv2.imshow("Image with Hello on It", Line)
cv2.waitKey(0)
cv2.destroyAllWindows()