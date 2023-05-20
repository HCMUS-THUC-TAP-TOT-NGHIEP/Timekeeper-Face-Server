import cv2
import os
from threading import Thread
from PIL import Image
import time
import numpy as np
from src.config import Config
import base64

def openCVToBase64(img):
    try:
        string = base64.b64encode(cv2.imencode('.png', img)[1]).decode()
        return string
    except Exception as ex:
        raise Exception(f"openCV2base64 failed. [exception{ex}]")
    
def base64ToOpenCV(str_img):
    try:
        image_data = bytes(str_img.split(",")[1], encoding="utf-8")
        np_data = np.frombuffer(base64.decodebytes(image_data), np.uint8)
        img = cv2.imdecode(np_data, cv2.IMREAD_ANYCOLOR)
        return img
    except Exception as ex:
        raise Exception(f"base64ToOpenCV failed. [exception{ex}]")

# lưu ảnh dạng png với đầu vào là mảng ảnh, id và tên vào datasets/raw/...
def save_images(images, id, name):
    try:
        path = os.path.join(os.getcwd(), "public", "datasets","raw",  f"{id}")
        if not os.path.isdir(path):
            os.makedirs(path)
        for i in range(len(images)):
            img_path = os.path.join(path, f"{i}.png")
            # region Convert base64 image to OpenCV image

            img = base64ToOpenCV(images[i])

            # endregion
            result = cv2.imwrite(img_path, img)
        return True

    except Exception as ex:
        raise Exception(f"save_images failed. [exception{ex}]")


# đếm số ảnh
def counter_img(path):
    try:
        imgcounter = 1
        imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
        for imagePath in imagePaths:
            time.sleep(0.008)
            imgcounter += 1
    except Exception as ex:
        raise Exception(f"counter_img failed. [exception{ex}]")


# cắt khuôn mặt từ ảnh lưu vào processed
def processed_faces(path_raw):
    try:
        detector = cv2.CascadeClassifier(Config.HAARCASCADEPATH)
        # đọc các id đã có
        for ID in os.listdir(path_raw):
            # path_raw_id = path_raw + "/" + ID
            path_raw_id = os.path.join(path_raw, ID) 
            path_processed_id = path_raw_id.replace("raw", "processed")
            # kiểm tra tồn tại của folder id
            if not os.path.isdir(path_processed_id):
                os.makedirs(path_processed_id)

            # duyệt các ảnh trong thư mục id
            for list in os.listdir(path_raw_id):
                # img_path = path_raw_id + "/" + list
                img_path = os.path.join(path_raw_id,list)
                img = cv2.imread(img_path)
                gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = detector.detectMultiScale(
                    gray_img, 1.3, 5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
                )
                for x, y, w, h in faces:
                    path_processed = img_path.replace("raw", "processed")
                    if not os.path.isdir(path_processed):
                        cv2.imwrite(path_processed, gray_img[y : y + h, x : x + w])
    except Exception as ex:
        raise Exception(f"processed_faces failed. [exception{ex}]")


# láy ảnh và nhãn từ mục ảnh processed
def getImagesAndLabels(path):
    try:
        # create empth face list
        faces = []
        # create empty ID list
        Ids = []
        for folder in os.listdir(path):
            # get the path of all the files in the folder
            folder_path = os.path.join(path, folder)
            imagePaths = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
            # list_names.append(folder)
            # now looping through all the image paths and loading the Ids and the images
            for imagePath in imagePaths:
                # loading the image and converting it to gray scale
                pilImage = Image.open(imagePath).convert("L")
                # Now we are converting the PIL image into numpy array
                imageNp = np.array(pilImage, "uint8")
                # getting the Id from the image
                Id = int(folder)
                # Id = int(folder)
                # extract the face from the training image sample
                faces.append(imageNp)
                Ids.append(Id)

        return faces, Ids
    except Exception as ex:
        raise Exception(f"getImagesAndLabels failed. [exception{ex}]")


# train ảnh khuôn mặt
def train_model(path_train):
    try:
        # ----------- train images function ---------------
        recognizer = cv2.face.LBPHFaceRecognizer_create()

        faces, Id = getImagesAndLabels(path_train)
        Thread(target=recognizer.train(faces, np.array(Id))).start()
        # Below line is optional for a visual counter effect
        Thread(target=counter_img(path_train)).start()
        recognizer.save(Config.PATH_MODEL_TRAIN)
        # print("All Images")
    except Exception as ex:
        raise Exception(f"train_model failed. [exception{ex}]")


# nhận dạng khuôn mặt từ 1 ảnh
def get_id_from_img(img):
    try:
        detector = cv2.CascadeClassifier(Config.HAARCASCADEPATH)
        # img = cv2.imread(image)
        clf = cv2.face.LBPHFaceRecognizer_create()
        clf.read(Config.PATH_MODEL_TRAIN)

        gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        features = detector.detectMultiScale(gray_image, 1.1, 10)

        for x, y, w, h in features:
            id, pred = clf.predict(gray_image[y : y + h, x : x + w])
            confidence = int(100 * (1 - pred / 300))
            if confidence > 70:
                return id
            else:
                return None
    except Exception as ex:
        raise Exception(f"get_id_from_img failed. [exception{ex}]")

def take_image(path="./public/datasets/raw"):
    try:
        cap = cv2.VideoCapture(0)
        counter_loop = 0
        counter_img = 0
        Id = input("nhap ma nhan vien: ")
        name = input("\nnhap ten nhan vien: ")
        # Id = "200"
        # name = "nguyen anh"

        folder_path = path + "/" + Id + "_" + name

        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
            print("tao forder thanh cong")

        while True:
            # Capture frame-by-frame
            ret, frame = cap.read()
            counter_loop += 1

            # Display the resulting frame
            cv2.imshow("frame", frame)
            if counter_loop % 5 == 0:
                counter_img += 1
                path_name = folder_path + "/" + str(counter_img) + ".jpg"
                cv2.imwrite(path_name, frame)
                print("Luu thanh cong")

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            if counter_loop >= 80:
                break

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()
    except Exception as ex:
        raise Exception(f"take_image failed. [exception{ex}]")


# def main():
#     # processed_faces(test_raw_path)
#     # train_model(test_train_path)
#     # img_path = "../../datasets/raw/SonTung/SonTung_0015.jpg"
#     # id = get_id_from_img(img_path)
#     # print(id)
#     take_image()


# if __name__ == '__main__':
#     main()
