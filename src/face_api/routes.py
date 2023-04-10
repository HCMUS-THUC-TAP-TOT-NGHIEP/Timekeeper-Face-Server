from datetime import datetime
from flask import Blueprint, current_app as app, request
from src.db import db
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.extension import ProjectException

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
        return {"Status": 0, "Description": None, "ResponseData": None}
    except ProjectException as pEx:
        pass
    except Exception as ex:
        pass
