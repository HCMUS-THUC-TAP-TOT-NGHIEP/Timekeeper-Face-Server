from src.db import db
from src import marshmallow
from marshmallow import fields
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean, BigInteger
from datetime import datetime
from src.services.DriveService import DriveService,  MimeType
from src.config import Config
import base64
import uuid
import os
import pickle
import face_recognition
from flask import current_app as app

class RecognitionData(db.Model):
    __tablename__ = "RecognitionData"
    Id = Column(BigInteger(), primary_key=True, autoincrement=True)
    EmployeeId = Column(Integer(), nullable=False)
    Key = Column(String())
    Url = Column(String())
    AccessUrl = Column(String())
    DownloadUrl = Column(String())
    CreatedAt = Column(DateTime(), default=datetime.now())
    CreatedBy = Column(Integer(), default=0)

    def __init__(self, employee_id, key, url, access_url, download_url, user_id):
        try:
            self.EmployeeId = employee_id
            self.Key = Key
            self.Url = url
            self.AccessUrl = access_url
            self.DownloadUrl = download_url
            db.session.add(self)
            db.session.flush()
            db.session.refresh(self)
            db.session.commit()
            return self.Id
        except Exception as ex:
            db.session.rollback()
            raise Exception(
                f'Không thể tạo object RecognitionData. Exception: {ex}')

    def __init__(self, employee_id, image_path, time: datetime, user_id: int = None, delete_after_save: bool = True):
        service = DriveService()
        try:
            self.EmployeeId = employee_id
            folder_name = time.__format__("%Y%m%d")
            folders = service.search_folder(
                query=f"(mimeType = '{MimeType.google_folder}') and (name = '{folder_name}') and ('{Config.DRIVE_FOLDER_ID}' in parents)")
            if folders is None or not folders:
                folder = service.create_folder(
                    folder_name=folder_name, parent_folder_id=Config.DRIVE_FOLDER_ID)
                if not folder:
                    return None
            else:
                folder = folders[0]
            file = service.upload_file(new_file_name=image_path,
                                       file_name=image_path, folder_id=folder["id"])
            if file is None:
                raise Exception(
                    "Không nhận được kết quả của lưu file lên google drive.")
            self.Key = file["id"]
            # self.Url = url
            self.AccessUrl = file["webViewLink"]
            self.DownloadUrl = file["webContentLink"]
            db.session.add(self)
            db.session.flush()
            db.session.refresh(self)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            raise Exception(
                f'Không thể tạo object RecognitionData. Exception: {ex}')
        finally:
            if delete_after_save:
                os.remove(image_path)
                pass
known_encodings = []
known_names = []

def openCVToBase64(img):
    try:
        # img_path = os.path.join(Config.RAW_PATH, Id, "0.png")
        # img = cv2.imread(img_path)
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

        flag = []

        for i in range(len(images)):
            # print(images)
            img_path = os.path.join(path, f"{i}.png")
            
            # region Convert base64 image to OpenCV image
            # image_data = bytes(images[i].split(",")[1], encoding="utf-8")
            # np_data = np.frombuffer(base64.decodebytes(image_data), np.uint8)
            # img = cv2.imdecode(np_data, cv2.IMREAD_ANYCOLOR)
            img = base64ToOpenCV(images[i])

            # endregion
            result = cv2.imwrite(img_path, img)
            flag.append(result)
        print(flag)
        return True

    except Exception as ex:
        raise Exception(f"save_images failed. [exception{ex}]")


# train ảnh khuôn mặt
def train_model_face(path_train):
    try:
        app.logger.info(f"train_model_face start {path_train}")
        for Id in os.listdir(path_train):
            Id_path = os.path.join(path_train, Id)
            
            # Loop through each image in the folder
            for file_path in os.listdir(Id_path):
                image_path = os.path.join(Id_path, file_path)
                image = face_recognition.load_image_file(image_path)
                
                # print(len(image))
                # Encode the face features
                encoding = face_recognition.face_encodings(image)
                if encoding == []:
                    continue
                encoding = encoding[0]
                print(image_path)
                # return 

                # Add the encoding and name to the lists
                known_encodings.append(encoding)
                known_names.append(Id)
                # Save the face encodings and names to a file
        with open("encodings.pickle", "wb") as f:
            pickle.dump({"encodings": known_encodings, "names": known_names}, f)
        app.logger.info("train_model_face OK")
        return known_encodings, known_names

    except Exception as ex:
        app.logger.exception(f"train_model_face failed, exception[{ex}]")
        raise Exception(f"train_model failed. [exception{ex}]")
    finally:
        app.logger.info(f"train_model_face finish {path_train}")


# nhận dạng khuôn mặt từ 1 ảnh
def get_id_from_img_face(img):
    try:
        # Load the face encodings and names from the file
        with open("encodings.pickle", "rb") as f:
            data = pickle.load(f)
            known_encodings = data["encodings"]
            known_names = data["names"]

        # Find face locations and encode the face features
        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)


        for face_encoding, face_location in zip(face_encodings, face_locations):

            # Compare the face encoding with the known encodings
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            
            # Find the index of the matched face
            match_index = matches.index(True) if True in matches else None
            print("start fine Id")
            # Get the name of the matched person: chỉ lấy khuôn mặt đầu tiên
            Id = known_names[match_index] if match_index is not None else "Unknown"
            return Id
    except Exception as ex:
        raise Exception(f"get_id_from_img failed. [exception{ex}]")

# # đếm số ảnh
# def counter_img(path):
#     try:
#         imgcounter = 1
#         imagePaths = [os.path.join(path, f) for f in os.listdir(path)]
#         for imagePath in imagePaths:
#             time.sleep(0.008)
#             imgcounter += 1
#     except Exception as ex:
#         raise Exception(f"counter_img failed. [exception{ex}]")


# # cắt khuôn mặt từ ảnh lưu vào processed
# def processed_faces(path_raw):
#     try:
#         detector = cv2.CascadeClassifier(Config.HAARCASCADEPATH)
#         # đọc các id đã có
#         for ID in os.listdir(path_raw):
#             # path_raw_id = path_raw + "/" + ID
#             path_raw_id = os.path.join(path_raw, ID) 
#             path_processed_id = path_raw_id.replace("raw", "processed")
#             # kiểm tra tồn tại của folder id
#             if not os.path.isdir(path_processed_id):
#                 os.makedirs(path_processed_id)

#             # duyệt các ảnh trong thư mục id
#             for list in os.listdir(path_raw_id):
#                 # img_path = path_raw_id + "/" + list
#                 img_path = os.path.join(path_raw_id,list)
#                 img = cv2.imread(img_path)
#                 gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#                 faces = detector.detectMultiScale(
#                     gray_img, 1.3, 5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE
#                 )
#                 for x, y, w, h in faces:
#                     path_processed = img_path.replace("raw", "processed")
#                     if not os.path.isdir(path_processed):
#                         cv2.imwrite(path_processed, gray_img[y : y + h, x : x + w])
#     except Exception as ex:
#         raise Exception(f"processed_faces failed. [exception{ex}]")


# láy ảnh và nhãn từ mục ảnh processed
# def getImagesAndLabels(path):
#     try:
#         # create empth face list
#         faces = []
#         # create empty ID list
#         Ids = []
#         for folder in os.listdir(path):
#             # get the path of all the files in the folder
#             folder_path = os.path.join(path, folder)
#             imagePaths = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
#             # list_names.append(folder)
#             # now looping through all the image paths and loading the Ids and the images
#             for imagePath in imagePaths:
#                 # loading the image and converting it to gray scale
#                 pilImage = Image.open(imagePath).convert("L")
#                 # Now we are converting the PIL image into numpy array
#                 imageNp = np.array(pilImage, "uint8")
#                 # getting the Id from the image
#                 Id = int(folder)
#                 # Id = int(folder)
#                 # extract the face from the training image sample
#                 faces.append(imageNp)
#                 Ids.append(Id)

#         return faces, Ids
#     except Exception as ex:
#         raise Exception(f"getImagesAndLabels failed. [exception{ex}]")


# def take_image(path="./public/datasets/raw"):
#     try:
#         cap = cv2.VideoCapture(0)
#         counter_loop = 0
#         counter_img = 0
#         Id = input("nhap ma nhan vien: ")
#         name = input("\nnhap ten nhan vien: ")
#         # Id = "200"
#         # name = "nguyen anh"

#         folder_path = path + "/" + Id + "_" + name

#         if not os.path.isdir(folder_path):
#             os.makedirs(folder_path)
#             print("tao forder thanh cong")

#         while True:
#             # Capture frame-by-frame
#             ret, frame = cap.read()
#             counter_loop += 1

#             # Display the resulting frame
#             cv2.imshow("frame", frame)
#             if counter_loop % 5 == 0:
#                 counter_img += 1
#                 path_name = folder_path + "/" + str(counter_img) + ".jpg"
#                 cv2.imwrite(path_name, frame)
#                 print("Luu thanh cong")

#             if cv2.waitKey(1) & 0xFF == ord("q"):
#                 break
#             if counter_loop >= 80:
#                 break

#         # When everything done, release the capture
#         cap.release()
#         cv2.destroyAllWindows()
#     except Exception as ex:
#         raise Exception(f"take_image failed. [exception{ex}]")


class RecognitionDataSchema(marshmallow.SQLAlchemyAutoSchema):
    Id = fields.Integer()
    EmployeeId = fields.Integer()
    # EmployeeInfo = fields.Method("get_employee_name")
    Key = fields.String()
    Url = fields.String()
    AccessUrl = fields.String()
    DownloadUrl = fields.String()
    CreatedAt = fields.DateTime()
    CreatedBy = fields.Integer()
