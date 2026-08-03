import os
import cv2
import numpy as np
from PIL import Image


def train_model():

    dataset_path = "dataset"
    trainer_path = "trainer"

    os.makedirs(trainer_path, exist_ok=True)

    recognizer = cv2.face.LBPHFaceRecognizer_create()

    detector = cv2.CascadeClassifier(
        "haarcascade_frontalface_default.xml"
    )

    faces = []
    ids = []

    for student_id in os.listdir(dataset_path):

        student_folder = os.path.join(dataset_path, student_id)

        if not os.path.isdir(student_folder):
            continue

        for image_name in os.listdir(student_folder):

            image_path = os.path.join(student_folder, image_name)

            try:
                img = Image.open(image_path).convert("L")
            except:
                continue

            img_numpy = np.array(img, "uint8")

            detected_faces = detector.detectMultiScale(img_numpy)

            for (x, y, w, h) in detected_faces:

                faces.append(img_numpy[y:y+h, x:x+w])
                ids.append(int(student_id))

    if len(faces) == 0:
        print("No face images found for training.")
        return False

    recognizer.train(faces, np.array(ids))

    recognizer.save("trainer/trainer.yml")

    print("Training Completed Successfully!")

    return True