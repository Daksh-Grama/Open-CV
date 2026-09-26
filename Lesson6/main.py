import os
from turtle import width                                                                                                
import cv2
from PIL import Image

path = "C:/Users/Daksh/Desktop/Open-CV-main/Lesson6/photos"
os.chdir(path)

mean_height = 0
mean_width = 0
images = []

for file in os.listdir('.'):
    if file.endswith(('.jpg', 'jpeg', '.png')):
        images.append(file)

num_of_images = len(images)
print(f"number of image are : {num_of_images}")

if num_of_images == 0:
    print("no images were found in this directory")

else:
    for file in images:
        img = Image.open(os.path.join(path, file))
        width, height = img.size
        mean_width = mean_width + width
        mean_height = mean_height + height
    mean_width = mean_width // num_of_images
    mean_height = mean_height // num_of_images
    print(f"Average Width : {mean_width}")
    print(f"AverageHeight : {mean_height}")

    for file in images :
        img = Image.open(os.path.join(path, file))
        width, height = img.size
        print(f"Original : {file} - {width}, {height}")
        imgResized = img.resize((mean_width, mean_height))

        imgResized.save(file, 'JPEG', quality = 95)
        print(file, "is resized")

    def VideoGenerator():
        videoname = "Scenary.avi"
        images = []

        for img in os.listdir('.'):
            if img.endswith(('.jpg', '.jpeg', '.png')):
                images.append(img)

        print("Images used for Video:")
        print(images)
        frame = cv2.imread(os.path.join(path, images[0]))
        height, width, layers = frame.shape
        video = cv2.VideoWriter(videoname, 0, 1, (width, height))

        for image in images:
            frame = cv2.imread(os.path.join(path, image))
            video.write(frame)

        video.release()

        cv2.destroyAllWindows()
        print("Video is generated successfully")
        print("Video is saved as", videoname)

VideoGenerator()

    
        
        



