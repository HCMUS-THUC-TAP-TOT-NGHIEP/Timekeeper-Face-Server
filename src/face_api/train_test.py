import cv2
import os
from threading import Thread
from PIL import Image
import time
import numpy as np
from sklearn.model_selection import train_test_split
import time
import random

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

#random số khác nhau
def create_num(arr, maxlength):
    random_num = random.randint(0, maxlength)
    for i in arr:
        while random_num == int(i):  # Kiểm tra số ngẫu nhiên có bằng số đã cho không
            random_num = random.randint(0, maxlength)  # Tạo lại số ngẫu nhiên nếu nó bằng số đã cho
    return random_num 

# láy ảnh và nhãn từ mục ảnh processed
def getImagesAndLabels(path):
    try:
        # create empth face list
        faces = []
        # create empty ID list
        Ids = []
        count_labels = 0
        for folder in os.listdir(path):
            # print("folder: ", folder)
            count = 0
            count_labels += 1
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
                # Id = int(folder[1:])
                Id = int(folder)
                
                # extract the face from the training image sample
                faces.append(imageNp)
                Ids.append(Id)
                count += 1
                if count == 10:
                    break
            if count_labels == 10:
                break

        return faces, Ids
    except Exception as ex:
        raise Exception(f"getImagesAndLabels failed. [exception{ex}]")

# nhận dạng khuôn mặt từ 1 ảnh
def get_id_from_img(img):
    try:

        clf = cv2.face.LBPHFaceRecognizer_create()
        clf.read("../../public/static/acc.yml")
        
        # gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        id, pred = clf.predict(img)
        confidence = int(100 * (1 - pred / 300))
        if confidence > 70:
            return id
        else:
            return None
    except Exception as ex:
        raise Exception(f"get_id_from_img failed. [exception{ex}]")

def target_(imagePaths):
    imgcounter = 1
    # imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
    for imagePath in imagePaths:
        time.sleep(0.008)
        imgcounter += 1

train_path = ["E:\\data\\Celebrity Faces Dataset\\processed",
              "E:\\test\\AT&T",
              "E:\\data\\Open Famous People Faces\\raw",
              "E:\\data\\LFW\\Detected Faces\\raw"]
# train ảnh khuôn mặt
def train_model():
    try:
        # ----------- train images function ---------------
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        # train_path = "E:\\data\\Celebrity Faces Dataset\\processed"
        faces, Ids = getImagesAndLabels(train_path[0])

        x_train, x_test, y_train, y_test = train_test_split(faces, Ids, test_size=0.2)

        Thread(target=recognizer.train(x_train, np.array(y_train))).start()
        # Below line is optional for a visual counter effect
        Thread(target=target_(y_train)).start()
        recognizer.save("../../public/static/acc.yml")
        return x_test, y_test
    except Exception as ex:
        raise Exception(f"train_model failed. [exception{ex}]")

def acc():
    named_tuple = time.localtime() # get struct_time
    time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    print("train_model start: ",time_string)

    x_test, y_test = train_model()

    named_tuple = time.localtime() # get struct_time
    time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    print("train_model end: ",time_string)
    # return 1

    Ids = []
    named_tuple = time.localtime() # get struct_time
    time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    print("test start: ",time_string)
    for r in range(len(y_test)):
        Id = get_id_from_img(x_test[r])
        # print("Id: ",Id)
        if Id is not None:
            Ids.append(Id)
        else:
            Ids.append(-1)
    named_tuple = time.localtime() # get struct_time
    time_string = time.strftime("%m/%d/%Y, %H:%M:%S", named_tuple)
    print("test end: ",time_string)
    y_test = np.array(y_test)
    Ids = np.array(Ids)
    correct = np.sum(y_test == Ids)
    return float(correct)/y_test.shape[0]

def main():
    accur = []
    for i in range(5):
        print("Testing: ", i)
        accuracy = acc()
        accur.append(accuracy)
        print("accuracy {}: ".format(i), accuracy)
    print("accuracy: ", accur)


if __name__ == "__main__":
    main()