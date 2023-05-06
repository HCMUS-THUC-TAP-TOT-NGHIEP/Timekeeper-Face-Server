from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request

from src.db import db
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.extension import ProjectException
from src.face_api.model import *

# from config import Config
from src.employee.model import EmployeeModel, employeeInfoSchema
from sqlalchemy import func, select

RAW_PATH = "./public/datasets/raw"
TRAIN_PATH = "./public/datasets/processed"

FaceApi = Blueprint("face", __name__)

# Luôn luôn viết try ... except...
# Ghi log:
#  - Thông tin (thành công, thực hiện task gì đó): app.logger.info(str)
#  - Lỗi, exception, project exception (ex): app.logger.error(str + {ex})

# HttpMethod api/face/...


# POST api/face/register
@FaceApi.route("/register", methods=["POST"])
def register():
    try:
        app.logger.info("register bắt đầu.")
        jsonRequestData = request.get_json()

        PictureList = (
            jsonRequestData["PictureList"] if "PictureList" in jsonRequestData else None
        )
        EmployeeId = (
            jsonRequestData["EmployeeId"] if "EmployeeId" in jsonRequestData else None
        )

        if not PictureList or len(PictureList) == 0:
            raise ProjectException("Không nhận được hình ảnh đăng ký")
        if not EmployeeId:
            raise ProjectException("Không nhận được mã nhân viên")

        employee = EmployeeModel.query.filter(EmployeeModel.Id == EmployeeId).first()
        if not employee:
            raise ProjectException(f"không tồn tại nhân viên [{EmployeeId}]")

        name = f"{employee.FirstName}_{employee.LastName}"
        # region Lưu local mảng ảnh đã nhận

        flag = save_images(PictureList, EmployeeId, name)
        if not flag:
            raise Exception("Không lưu được ảnh")
        app.logger.info("save_images successfully. Lưu ảnh thành công")

        #endregion

        # region quá trình trích xuất khuôn mặt và train ảnh
        # processed_faces(RAW_PATH)
        train_model_face(RAW_PATH)

        #endregion

        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }
    except ProjectException as pEx:
        app.logger.error(f"Đăng ký khuôn mặt thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"2. Đăng ký khuôn mặt không thành công. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.error(f"Đăng ký khuôn mặt thất bại. Có exception[{ex}]")
        return {
            "Status": 0,
            "Description": f"3. Có lỗi ở máy chủ",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("register kết thúc.")


# POST api/face/recognition
# https://helpex.vn/question/python-opencv-hinh-anh-thanh-chuoi-byte-de-chuyen-json-60cecfa5f137b0e523f9cce4
@FaceApi.route("/recognition", methods=["POST"])
def recognition():
    try:
        app.logger.info("recognition bắt đầu.")
        jsonRequestData = request.get_json()
        Picture = (
            jsonRequestData["Picture"] if "Picture" in jsonRequestData else None
        )
        img = base64ToOpenCV(Picture)
        Id = get_id_from_img_face(img)

        if Id == None:
            raise ProjectException(
                "Khuôn mặt hiện tại chưa đăng ký hoặc nhận diện sai."
            )
        
        employee = EmployeeModel.query.filter(EmployeeModel.Id == Id).first()
        name = f"{employee.FirstName}_{employee.LastName}"

        app.logger.info("EmployeeID:" + str(Id))

        list_img = os.listdir(os.path.join(Config.RAW_PATH, str(Id)))
        img_path = os.path.join(Config.RAW_PATH, str(Id), list_img[0])

        img = cv2.imread(img_path)
        str_img = openCVToBase64(img)
        app.logger.info(f"Recognition thành công nhân viên Id[{Id}]")

        return {
            "Status": 1,
            "Description": "Nhận diện thành công.",
            "ResponseData": {
                "Id": Id,
                "Name": name,
                "Img": str_img
            },
        }
            

    except ProjectException as pEx:
        app.logger.error(f"Nhận diện khuôn mặt thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Nhận diện không thành công. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.error(f"Nhận diện khuôn mặt thất bại. Có exception[{ex}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Nhận diện khuôn mặt không thành công",
            "ResponseData": None,
        }, 200
