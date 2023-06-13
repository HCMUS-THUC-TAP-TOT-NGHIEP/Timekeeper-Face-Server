from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request

from src.db import db
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.extension import ProjectException
from src.face_api.actions import *
from src.employee.model import EmployeeModel, employeeInfoSchema
from src.employee_checkin.EmployeeCheckin import EmployeeCheckin, employeeCheckinSchema, employeeCheckinListSchema
from sqlalchemy import func, select
from keras_facenet import FaceNet
from sklearn.preprocessing import LabelEncoder
import threading

from src.face_api.train_facenet import train_facenet
from src.face_api.face_recog import get_ID

FaceApi = Blueprint("face", __name__)

embedder = FaceNet()
encoder = LabelEncoder()

# Luôn luôn viết try ... except...
# Ghi log:
#  - Thông tin (thành công, thực hiện task gì đó): app.logger.info(str)
#  - Lỗi, exception, project exception (ex): app.logger.error(str + {ex})

# HttpMethod api/face/...


# POST api/face/register
@FaceApi.route("/register", methods=["POST"])
@admin_required()
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
        # Lưu local mảng ảnh đã nhận

        flag = save_images(PictureList, EmployeeId, name)
        if not flag:
            raise Exception("Không lưu được ảnh")
        app.logger.info("save_images successfully. Lưu ảnh thành công")

        

        # quá trình trích xuất khuôn mặt và train ảnh
        # train_facenet(embedder, encoder, Config.LOCAL_STORAGE, Config.PATH_ENCODE, Config.PATH_MODEL)        
        t = threading.Thread(target=train_facenet, args=(embedder, encoder, Config.LOCAL_STORAGE,Config.PATH_ENCODE, Config.PATH_MODEL ))
        t.start()

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
            "Description": f"3. Xảy ra lỗi ở máy chủ",
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
        # region: Khai báo

        Picture = (
            jsonRequestData["Picture"] if "Picture" in jsonRequestData else None
        )
        AttendanceTime = (
            jsonRequestData["AttendanceTime"] if "AttendanceTime" in jsonRequestData else datetime.now()
        )

        #endregion
        
        #region validation

        if not Picture or len(Picture) == 0:
            raise ProjectException("Yêu cầu không hợp lệ do không cung cấp hình ảnh.")        
        if not AttendanceTime :
            raise ProjectException("Yêu cầu không hợp lệ do thời gian nhận diện không có hoặc không hợp lệ.")
        
        #endregion

        RecognitionMethod = 1
        img = base64ToOpenCV(Picture)
        Id = get_ID(embedder, encoder, Config.PATH_ENCODE, Config.PATH_MODEL, img)

        if Id == -1:
            raise ProjectException(
                "Khuôn mặt hiện tại chưa đăng ký hoặc nhận diện sai."
            )
        
        employee = EmployeeModel.query.filter(EmployeeModel.Id == Id).first()
        if not employee:
            raise ValueError(f"Không tìm thấy nhân viên mã {Id}")
        name = f"{employee.LastName} {employee.FirstName}"
        # latestCheckin = EmployeeCheckin.query.filter_by(and_(
        #     func.extract('epoch',
        #         Time,
        #         AttendanceTime
        #     ) > 5
        # )).first()
        # if not latestCheckin:
        employeeCheckin = EmployeeCheckin()
        employeeCheckin.Method = RecognitionMethod
        employeeCheckin.MethodText = "Khuôn mặt"
        employeeCheckin.EmployeeId = employee.Id
        employeeCheckin.Time = AttendanceTime
        employeeCheckin.EvidenceId = None
        employeeCheckin.LogType = 0
        employeeCheckin.CreatedAt = datetime.now()
        employeeCheckin.CreatedBy = 0
        employeeCheckin.ModifiedAt = datetime.now()
        employeeCheckin.ModifiedBy = 0
        db.session.add(employeeCheckin)

        app.logger.info("EmployeeID:" + str(Id))

        list_img = os.listdir(os.path.join(Config.LOCAL_STORAGE, str(Id)))
        img_path = os.path.join(Config.LOCAL_STORAGE, str(Id), list_img[0])

        img = cv2.imread(img_path)
        str_img = openCVToBase64(img)
        db.session.commit()
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
            "Description": f"Xảy ra lỗi ở máy chủ. Nhận diện khuôn mặt không thành công",
            "ResponseData": None,
        }, 200
