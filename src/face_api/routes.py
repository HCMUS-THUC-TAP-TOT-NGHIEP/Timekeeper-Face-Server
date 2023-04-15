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
        processed_faces(RAW_PATH)
        train_model(TRAIN_PATH)

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
@FaceApi.route("/recognition", methods=["POST"])
def recognition():
    try:
        jsonRequestData = request.get_json()
        PictureList = (
            None
            if "PictureList" not in jsonRequestData
            else jsonRequestData["PictureList"]
        )
        ids = []
        for img in PictureList:
            id = get_id_from_img(img)
            ids.append(id)
        if id:
            name = ""
            return {
                "Status": 1,
                "Description": "Nhận diện thành công.",
                "ResponseData": {name},
            }
        else:
            raise ProjectException(
                "Khuôn mặt hiện tại chưa đăng ký hoặc nhận diện sai."
            )

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
