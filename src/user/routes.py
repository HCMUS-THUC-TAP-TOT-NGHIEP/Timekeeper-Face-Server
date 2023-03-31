from src.db import db
from flask import Blueprint, current_app as app, request
from src.jwt import jwt_required, get_jwt_identity, get_jwt
from src.middlewares.token_required import admin_required
from sqlalchemy import select, or_
from src.authentication.model import UserModel
from src.employee.model import EmployeeModel
from src.extension import ProjectException
from src import bcrypt
from datetime import datetime

User = Blueprint("user", __name__)


# GET api/user
@User.route("", methods=["GET"])
@jwt_required()
def authorization():
    try:
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"Email": email, "Username": username},
        }
    except Exception as ex:
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Failed to reset password.",
            "ResponseData": None,
        }

# GET api/user/list
@User.route("/list", methods=["POST"])
@admin_required()
def GetUserList():
    try:
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        jsonRequestData = request.get_json()
        page = 1 if "Page" not in jsonRequestData else jsonRequestData["Page"]
        perPage = 10 if "PerPage" not in jsonRequestData else jsonRequestData["PerPage"]
        accountIdList = db.paginate(
            select(
                UserModel.Id,
            )
            .join(EmployeeModel, EmployeeModel.Id == UserModel.EmployeeId, isouter=True)
            .order_by(UserModel.Id),
            page=page,
            per_page=perPage,
        )
        accountList = db.session.execute(
            select(
                UserModel.Id,
                UserModel.Username,
                UserModel.EmailAddress,
                UserModel.CreatedAt,
                UserModel.Name,
                UserModel.EmployeeId,
                (EmployeeModel.FirstName + " " + EmployeeModel.LastName).label(
                    "Employee"
                ),
            )
            .join(EmployeeModel, EmployeeModel.Id == UserModel.EmployeeId, isouter=True)
            .where(UserModel.Id.in_(list(map(lambda x: int(x), accountIdList.items))))
            .order_by(UserModel.Id)
        ).all()
        response = {
            "AccountList": [dict(r) for r in accountList],
            "Total": accountIdList.total,
            "TotalPages": accountIdList.pages,
            "CurrentPage": accountIdList.page,
        }
        app.logger.info(f"Truy vấn danh sách account thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": response,
        }
    except Exception as ex:
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Không thể truy vấn danh sách các user/ account.",
            "ResponseData": None,
        }


@User.route("/add", methods=["POST"])
@admin_required()
def AddNewUser():
    try:
        claims = get_jwt()
        email = claims["email"]
        id = claims["id"]

        jsonRequestData = request.get_json()

        # region validate

        if "Username" not in jsonRequestData:
            raise ProjectException("Chưa cung cấp username.")
        if "Password" not in jsonRequestData:
            raise ProjectException("Chưa cung cấp mật khẩu.")
        if "EmailAddress" not in jsonRequestData:
            raise ProjectException("Chưa cung cấp email.")
        # if "Role" in jsonRequestData:
        #     raise ProjectException("Chưa chọn phân quyền.")

        # endregion

        # region declare

        username = jsonRequestData["Username"]
        password = jsonRequestData["Password"]
        email = jsonRequestData["EmailAddress"]
        # role = jsonRequestData['Role']
        name = None if "Name" not in jsonRequestData else jsonRequestData["Name"]

        # endregion

        exist = db.session.execute(
            select(UserModel).where(
                or_(UserModel.Username == username, UserModel.EmailAddress == email)
            )
        ).first()
        if exist:
            raise ProjectException(
                f'Username "{username}" hoặc email "{email}" đã được sử dụng.'
            )
        newUser = UserModel()
        newUser.Username = username
        newUser.EmailAddress = email
        newUser.PasswordHash = bcrypt.generate_password_hash(password).decode("utf-8")
        newUser.Name = name
        newUser.CreatedAt = datetime.now()
        newUser.CreatedBy = id
        newUser.Status = "1"
        db.session.add(newUser)
        db.session.commit()
        app.logger.info(f"Truy vấn danh sách account thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"Id": newUser.Id},
        }
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"AddNewUser có lỗi. {pEx}")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. \nKhông thể thêm user mới.",
            "ResponseData": None,
        }


@User.route("/delete", methods=["DELETE"])
@admin_required()
def DeleteUser():
    try:
        claims = get_jwt()
        email = claims["email"]
        id = claims["id"]

        jsonRequestData = request.get_json()
        # region validation

        if "Username" not in jsonRequestData:
            raise ProjectException("Chưa cung cấp mã user")

        # endregion

        username = jsonRequestData["Username"]
        exist = (
            db.session.query(UserModel).filter(UserModel.Username == username).first()
        )
        if not exist:
            raise ProjectException("Tài khoản đã bị thay đổi hoặc xóa bới người khác.")
        if exist.Id == id:
            raise ProjectException("Tài khoản đang được sử dụng, không thể xóa.")

        db.session.delete(exist)
        db.session.commit()
        app.logger.info(f"Đã xóa account [{exist.Username}]/ [{exist.EmailAddress}]")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }

    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"AddNewUser có lỗi. {pEx}")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. \nKhông thể xóa người dùng.",
            "ResponseData": None,
        }


@User.route("/update", methods=["PUT"])
@admin_required()
def UpdateUser():
    try:
        claims = get_jwt()
        email = claims["email"]
        id = claims["id"]

        jsonRequestData = request.get_json()
        # region validation

        if "Username" not in jsonRequestData:
            raise ProjectException("Chưa cung cấp mã user")

        # endregion
        username = jsonRequestData["Username"]
        exist = db.session.execute(
            db.select(UserModel).filter_by(Username=username)
        ).scalar_one_or_none()
        if not exist:
            raise ProjectException(
                'Tài khoản "' + username + '" đã bị thay đổi hoặc xóa bởi người khác'
            )

        hasSomeChanges = False

        for key in jsonRequestData:
            if getattr(exist, key) != jsonRequestData[key]:
                hasSomeChanges = True
                setattr(exist, key, jsonRequestData[key])
        if not hasSomeChanges:
            raise ProjectException(
                f"Không thông tin thay đổi trong người dùng [{username}]"
            )
        exist.ModifiedAt = datetime.now()
        exist.ModifiedBy = id
        db.session.commit()
        app.logger.info(f"UpdateUser username[{username}] thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200

    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"AddNewUser có lỗi. {pEx}")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. \nKhông thể thay đổi thông tin người dùng.",
            "ResponseData": None,
        }
