import os 
import cv2
from PIL import Image

path = "C:/Users/Daksh/Desktop/Open-CV-main/Lesson6/photos"
os.chdir(path)

mean_height = 0
mean_weight = 0
images = []

for file in os.listdir('.'):
    if file.endswith(('.jpg', 'jpeg', '.png')):
        images.append(file)

num_of_images = len(images)
print(f"number of image are : {num_of_images}")

if num_of_images == 0:
    print("no images were found in this directory")

print(images)
