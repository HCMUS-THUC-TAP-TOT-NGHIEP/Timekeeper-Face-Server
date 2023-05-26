from src.db import db
from flask import Blueprint, current_app as app, request
from src.jwt import jwt_required, get_jwt_identity, get_jwt
from src.middlewares.token_required import admin_required
from sqlalchemy import select, or_, and_
from src.authentication.model import UserModel
from src.employee.model import EmployeeModel
from src.extension import ProjectException, object_as_dict

# from src import bcrypt
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
            "AccountList": [r._asdict() for r in accountList],
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

#  POST api/user/add
@User.route("/add", methods=["POST"])
@admin_required()
def AddNewUser():
    try:
        # region declare

        claims = get_jwt()
        adminUsername = claims["username"]
        id = claims["id"]
        jsonRequestData = request.get_json()
        username = (
            jsonRequestData["Username"] if "Username" in jsonRequestData else None
        )
        password = (
            jsonRequestData["Password"] if "Password" in jsonRequestData else None
        )
        email = (
            jsonRequestData["EmailAddress"]
            if "EmailAddress" in jsonRequestData
            else None
        )
        name = jsonRequestData["Name"] if "Name" in jsonRequestData else None
        confirmPassword = (
            jsonRequestData["ConfirmPassword"]
            if "ConfirmPassword" in jsonRequestData
            else None
        )
        # role = jsonRequestData['Role']

        # endregion

        # region validate

        if not username or not username.strip():
            raise ProjectException("Chưa cung cấp username.")
        if not password or not password.strip():
            raise ProjectException("Chưa cung cấp mật khẩu.")
        if not email or not email.strip():
            raise ProjectException("Chưa cung cấp email.")
        # if "Role" in jsonRequestData:
        #     raise ProjectException("Chưa chọn phân quyền.")
        if not confirmPassword or not confirmPassword.strip():
            raise ProjectException("Chưa cung cấp mật khẩu xác thực.")

        # endregion

        adminUser = UserModel.query.filter(
            and_(UserModel.Username == adminUsername, UserModel.Id == id)
        ).first()
        if not adminUser:
            app.logger.error(f"Người dùng {adminUsername} đã bị thay đổi hoặc xóa.")
            return {
                "Status": 0,
                "Description": f"Người dùng {adminUsername} đã bị thay đổi hoặc xóa.",
                "ResponseData": None,
            }, 500
        if not adminUser.verify_password(confirmPassword):
            raise ProjectException(
                f"Xác thực không thành công! Vui lòng kiểm tra lại mật khẩu!"
            )

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
        newUser.password = password
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


# PUT: api/user/update
@User.route("/update", methods=["PUT"])
@admin_required()
def UpdateUser():
    try:
        # region Khai báo
        claims = get_jwt()
        email = claims["email"]
        username = claims["username"]
        id = claims["id"]
        jsonRequestData = request.get_json()
        targetUser = (
            jsonRequestData["Username"] if "Username" in jsonRequestData else None
        )
        confirmPassword = (
            jsonRequestData["ConfirmPassword"]
            if "ConfirmPassword" in jsonRequestData
            else None
        )

        # endregion

        # region validation

        if not targetUser or not targetUser.strip():
            raise ProjectException("Chưa cung cấp mã user")
        if not confirmPassword or not confirmPassword.strip():
            raise ProjectException("Chưa cung cấp mật khẩu xác thực.")

        # endregion

        # region authentication

        user = UserModel.query.filter(
            or_(UserModel.Username == username, UserModel.EmailAddress == email)
        ).first()

        if not user:
            app.logger.error(f"Người dùng {username} đã bị thay đổi hoặc xóa.")
            return {
                "Status": 0,
                "Description": f"Người dùng {username} đã bị thay đổi hoặc xóa.",
                "ResponseData": None,
            }, 500

        if not user.verify_password(confirmPassword):
            raise ProjectException(
                f"Xác thực không thành công! Vui lòng kiểm tra lại mật khẩu!"
            )

        # endregion

        target = db.session.execute(
            db.select(UserModel).filter_by(Username=targetUser)
        ).scalar_one_or_none()
        if not target:
            raise ProjectException(
                'Tài khoản "' + targetUser + '" đã bị thay đổi hoặc xóa bởi người khác'
            )

        hasSomeChanges = False
        for key in jsonRequestData:
            if (
                key != "ConfirmPassword"
                and getattr(target, key) != jsonRequestData[key]
            ):
                hasSomeChanges = True
                setattr(target, key, jsonRequestData[key])
        if not hasSomeChanges:
            raise ProjectException(
                f"Không có thông tin thay đổi trong người dùng [{targetUser}]"
            )
        target.ModifiedAt = datetime.now()
        target.ModifiedBy = id
        db.session.commit()
        app.logger.info(f"UpdateUser username[{targetUser}] thành công")
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
