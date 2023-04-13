from datetime import datetime
from flask import Blueprint, current_app as app, request
from src.db import db
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.extension import ProjectException
from src.face_api.model import *
from config import Config



FaceApi = Blueprint("face", __name__)

# Luôn luôn viết try ... except...
# Ghi log:
#  - Thông tin (thành công, thực hiện task gì đó): app.logger.info(str)
#  - Lỗi, exception, project exception (ex): app.logger.error(str + {ex})

# HttpMethod api/face/...

# POST api/face/register
FaceApi.route("/register", methods=["POST"])
def register():
    try:
        processed_faces(Config.TEST_RAW_PATH)
        train_model(Config.TEST_TRAIN_PATH)
        return {"Status": 1, "Description": "Đăng ký khuôn mặt thành công.", "ResponseData": None}
    except ProjectException as pEx:
        app.logger.error(f"Đăng ký khuôn mặt thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Đăng ký khuôn mặt không thành công. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.error(f"Đăng ký khuôn mặt thất bại. Có exception[{ex}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Đăng ký khuôn mặt không thành công",
            "ResponseData": None,
        }, 200

# POST api/face/recognition
FaceApi.route("/recognition", methods=["POST"])
def recognition():
    try:
        img = ""
        id = get_id_from_img(img)
        if id:
            name = ""
            return {"Status": 1, "Description": "Nhận diện thành công.", "ResponseData": {name}}
        else:
            raise ProjectException (
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
