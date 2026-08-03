import cv2
import os
import numpy as np
from PIL import Image

# Create trainer folder if it doesn't exist
if not os.path.exists("trainer"):
    os.makedirs("trainer")

recognizer = cv2.face.LBPHFaceRecognizer_create()

detector = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")


def getImagesAndLabels(path):
    faceSamples = []
    ids = []

    for student_folder in os.listdir(path):

        folder_path = os.path.join(path, student_folder)

        if not os.path.isdir(folder_path):
            continue

        for image_name in os.listdir(folder_path):

            image_path = os.path.join(folder_path, image_name)

            gray_image = Image.open(image_path).convert('L')

            img_numpy = np.array(gray_image, 'uint8')

            faces = detector.detectMultiScale(img_numpy)

            for (x, y, w, h) in faces:
                faceSamples.append(img_numpy[y:y+h, x:x+w])
                ids.append(int(student_folder))

    return faceSamples, ids


faces, ids = getImagesAndLabels("dataset")

recognizer.train(faces, np.array(ids))

recognizer.save("trainer.yml")

print("Training Completed Successfully!")
