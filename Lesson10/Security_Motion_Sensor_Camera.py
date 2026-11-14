import cv2
import numpy as np
import time
sec = cv2.VideoCapture(0)
if not sec.isOpened():
    print("Camera is not found!")
    exit()
bg =cv2.createBackgroundSubtractorMOG2(history = 500, varThreshold = 50, detectShadows = True)
