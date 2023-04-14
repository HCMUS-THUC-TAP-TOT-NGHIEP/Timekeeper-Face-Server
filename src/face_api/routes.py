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
from src.employee.model import EmployeeModel
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
        jsonRequestData = request.get_json()

        PictureList = None if "PictureList" not in jsonRequestData else jsonRequestData["PictureList"]
        EmployeeId = None if "EmployeeId" not in jsonRequestData else jsonRequestData["EmployeeId"]
        
        exit = db.session.execute(
            db.select(EmployeeModel).filter_by(Id=EmployeeId)
        ).scalar_one_or_none()
        
        if PictureList:
            if exit:
                name = db.session.execute(
                    select(
                        func.concat(EmployeeModel.FirstName, " ", EmployeeModel.LastName).label("ManagerName")
                    )
                    .select_from(EmployeeModel)
                    .where(EmployeeModel.Id == EmployeeId)
                )

                # Lưu local mảng ảnh đã nhận 
                save_images(PictureList, EmployeeId, name)
            else:
                raise ProjectException(
                    "không tồn tại Id {EmployeeId}"
                )
        else:
            raise ProjectException(
                "Không nhận được hình ảnh đăng ký"
            )
        
        # quá trình trích xuất khuôn mặt và train ảnh
        print("Registering")
        processed_faces(RAW_PATH)
        train_model(TRAIN_PATH)

        return {
            "Status": 1, 
            "Description": "1. Đăng ký khuôn mặt thành công.", 
            "ResponseData": None
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
            "Description": f"3. Có lỗi ở máy chủ. Đăng ký khuôn mặt không thành công",
            "ResponseData": None,
        }, 200
    finally:
        pass


# POST api/face/recognition
@FaceApi.route("/recognition", methods=["POST"])
def recognition():
    try:
        jsonRequestData = request.get_json()
        PictureList = None if "PictureList" not in jsonRequestData else jsonRequestData["PictureList"]
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
