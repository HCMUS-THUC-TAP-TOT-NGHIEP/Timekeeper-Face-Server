from src.db import db
from flask import Blueprint, current_app as app, request
from src.jwt import jwt_required, get_jwt_identity, get_jwt
from src.middlewares.token_required import admin_required
from sqlalchemy import select, or_, and_, func
from src.authentication.model import UserModel
from src.employee.model import EmployeeModel
from src.utils.extension import ProjectException, object_as_dict
from src.user.model import UserSchema, RoleSchema, RoleModel

# from src import bcrypt
from datetime import datetime

User = Blueprint("user", __name__)

# GET api/user
@User.route("", methods=["GET"])
@jwt_required()
def GetUserInfo():
    try:
        claims = get_jwt()
        user_id = claims["id"]
        identity = get_jwt_identity()
        username = identity["username"]
        current_user = UserModel.query.filter_by(Id=user_id).first()
        if not current_user:
            raise ProjectException(f"Người dùng {username} đã bị thay đổi hoặc xóa bởi người khác.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "User": UserSchema().dump(current_user)
            }
        }
    except ProjectException as pEx:
        app.logger.exception(f"GetUserInfo có lỗi. {pEx}")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }
    except Exception as ex:
        app.logger.exception(f"GetUserInfo có lỗi. {ex}")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Hãy kiểm tra log.",
            "ResponseData": None,
        }
    finally:
        app.logger.info(f"GetUserInfo finish.")


# GET api/user/authorization
@User.route("authorization", methods=["GET"])
@jwt_required()
def get_authorization():
    try:
        app.logger.info(f"check_authorization start.")
        identity = get_jwt_identity()
        claim = get_jwt()
        user_id = claim["id"]
        username = identity["username"]
        args = request.args
        target = args["Target"] if "Target" in args else None
        permission = args["Permission"] if "Permission" in args else None
        current_user = UserModel.query.filter_by(Id=user_id).first()
        if not current_user:
            raise ProjectException(f"Người dùng {username} đã bị thay đổi hoặc xóa bởi người khác.")
        role = RoleModel.query.filter_by(Id=current_user.Role).first()
        if not role:
            raise ProjectException(f"Phân quyền cho người dùng {username} đã bị thay đổi hoặc xóa bởi người khác.")

        response = {
                    "Status": 1,
                    "Description": None,
                    "ResponseData": {
                        "Authorization": {}
                    }
        }

        if target == "User":
            if role.Id == 1:
                response["ResponseData"]["Authorization"] = {
                    "User": {
                        "create": True,
                        "read": True,
                        "update": True,
                        "delete": True,
                    }
                }
            else:
                response["ResponseData"]["Authorization"] = {
                    "User": {
                        "create": False,
                        "read": True,
                        "update": False,
                        "delete": False,
                    }
                }

        elif target == "Employee": 
            if role.Id == 1 or role.Id == 2:
                response["ResponseData"]["Authorization"] = {
                    "Employee": {
                        "create": True,
                        "read": True,
                        "update": True,
                        "delete": True,
                    }
                }
            else:
                response["ResponseData"]["Authorization"] = {
                    "Employee": {
                        "create": False,
                        "read": False,
                        "update": False,
                        "delete": False,
                    }
                }

        elif target == "Department": pass
        elif target == "Shift": pass
        elif target == "ShiftAssignment": pass
        elif target == "Timesheet": pass
        else: pass

        return response

    except ProjectException as pEx:
        app.logger.exception(f"check_authorization có lỗi. {pEx}")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }
    except Exception as ex:
        app.logger.exception(f"check_authorization có lỗi. {ex}")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Hãy kiểm tra log.",
            "ResponseData": None,
        }
    finally:
        app.logger.info(f"check_authorization finish.")

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
        searchString = "" if "SearchString" not in jsonRequestData else jsonRequestData["SearchString"]
        
        query = db.select(UserModel)
        if searchString and searchString.strip():
            sqlStr = "%" + searchString.upper() + "%"
            query = query.where(or_(func.upper(UserModel.Username).like(sqlStr), func.upper(UserModel.EmailAddress).like(sqlStr)))
        query = query.order_by(UserModel.CreatedAt)        

        accountIdList = db.paginate(query, page=page, per_page=perPage)
        
        response = {
            "AccountList": UserSchema(many=True).dump(accountIdList.items),
            "Total": accountIdList.total,       
            "TotalPages": accountIdList.pages,
            "CurrentPage": accountIdList.page,
        }
        app.logger.info(f"GetUserList successfully.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": response,
        }
    except Exception as ex:
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Hãy kiểm tra log.",
            "ResponseData": None,
        }

#  POST api/user/add
@User.route("/add", methods=["POST"])
@admin_required()
def AddNewUser():
    try:
        # region declare

        claims = get_jwt()
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
        role = jsonRequestData["Role"] if "Role" in jsonRequestData else None

        # endregion

        # region validate

        if not username or not username.strip():
            raise ProjectException("Chưa cung cấp username.")
        if not password or not password.strip():
            raise ProjectException("Chưa cung cấp mật khẩu.")
        if not email or not email.strip():
            raise ProjectException("Chưa cung cấp email.")
        if not role:
            raise ProjectException("Chưa phân quyền cho tài khoản.")
        if not confirmPassword or not confirmPassword.strip():
            raise ProjectException("Chưa cung cấp mật khẩu xác thực.")

        # endregion

        adminUser = UserModel.query.filter(
            and_(UserModel.Id == id)
        ).first()
        if not adminUser:
            app.logger.error(f"Tài khoản của bạn không tồn tại, đã bị thay đổi hoặc xóa.")
            return {
                "Status": 0,
                "Description": f"Tài khoản của bạn không tồn tại.",
                "ResponseData": None,
            }, 500
        if not adminUser.verify_password(confirmPassword):
            raise ProjectException(
                f"Xác thực mật khẩu không đúng."
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
        newUser.Role = role
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
            "Description": f"Xảy ra lỗi ở máy chủ. \nKhông thể thêm user mới.",
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
            "Description": f"Xảy ra lỗi ở máy chủ. \nKhông thể xóa người dùng.",
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

        # hasSomeChanges = False
        for key in jsonRequestData:
            if (
                key != "ConfirmPassword"
                and getattr(target, key) != jsonRequestData[key]
            ):
                hasSomeChanges = True
                setattr(target, key, jsonRequestData[key])
        # if not hasSomeChanges:
        #     raise ProjectException(
        #         f"Không có thông tin thay đổi trong người dùng [{targetUser}]"
        #     )
        target.ModifiedAt = datetime.now()
        target.ModifiedBy = id
        db.session.commit()
        app.logger.info(f"UpdateUser username[{targetUser}] thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "User":  UserSchema().dump(target),
            },
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
            "Description": f"Xảy ra lỗi ở máy chủ. \nKhông thể thay đổi thông tin người dùng.",
            "ResponseData": None,
        }

# GET: api/user/role
@User.route("role", methods=["GET"])
@jwt_required()
def GetUserRoleList():
    try: 
        result = db.session.execute(db.select(RoleModel).order_by(RoleModel.Id)).scalars().all()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "RoleList": RoleSchema(many=True).dump(result),
                "Total": len(result)
            },
        }

    except ProjectException as pEx:
        app.logger.exception(f"GetUserRoleList có lỗi. {pEx}")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }
    except Exception as ex:
        app.logger.exception(f"GetUserRoleList có lỗi. {ex}")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Vui lòng kiểm tra log.",
            "ResponseData": None,
        }
