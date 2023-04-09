import re
from datetime import datetime
from urllib.parse import urljoin
from flask import Blueprint
from flask import current_app as app
from flask import render_template, request
# from src import bcrypt
from src.authentication.model import UserModel, UserSchema
from src.db import db
from src.email import send_email
from src.extension import ProjectException
from src.jwt import (
    TokenBlockList,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import select, or_, and_

Authentication = Blueprint("auth", __name__)

userSchema = UserSchema()


# GET api/auth/register
@Authentication.route("/register", methods=["POST"])
def register():
    try:
        jsonRequestData = request.get_json()
        email = None if "Email" not in jsonRequestData else jsonRequestData["Email"]
        username = None if "Username" not in jsonRequestData else jsonRequestData["Username"]
        password = None if "Password" not in jsonRequestData else jsonRequestData["Password"]
        # region validate

        if not username or not isinstance(username, str) or  not username.strip():
            raise ProjectException(
                "Vui lòng cung cấp Username hợp lệ."
            )    
        if  not email or not isinstance(email, str) or not email.strip():
            raise ProjectException(
                "Vui lòng cung cấp email hợp lệ."
            )
        emailRegex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(emailRegex, email):
            raise ProjectException(f"Email {email} không hợp lệ.")
        if not password or not isinstance(password, str) or not password.strip():
            raise ProjectException(
                "Vui lòng cung cấp mật khẩu."
            )

        # endregion

        users = UserModel.query.all()
        if len(users) == 0:
            # hashedPassword = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = UserModel()
            new_user.EmailAddress = email
            new_user.Username = username
            new_user.password = password
            new_user.Status = 1
            new_user.Role = 1
            new_user.CreatedBy = 0
            new_user.CreatedAt = datetime.now()
            new_user.ModifiedBy = 0
            new_user.ModifiedAt = datetime.now()
            db.session.add(new_user)
            db.session.commit()
            return {"Status": 1, "Description": None, "ResponseData": None}
        exist = UserModel.query.filter(or_(UserModel.EmailAddress == email, UserModel.Username==username)).first()
        if not exist:
            if not isinstance(jsonRequestData["adminId"], str):
                raise Exception("Admin ID is not valid")
            if not isinstance(jsonRequestData["role"], str):
                raise Exception("Role is not valid")
            role = int(jsonRequestData["role"])
            adminId = int(jsonRequestData["adminId"])
            # hashedPassword = bcrypt.generate_password_hash(password).decode("utf-8")
            # new_user = UserModel(email, hashedPassword, "", 1, status=1, role=role)
            new_user = UserModel()
            new_user.Username = username
            new_user.EmailAddress = email
            new_user.password = password
            new_user.Status = 1
            new_user.Role = role
            new_user.CreatedBy = adminId
            new_user.CreatedAt = datetime.now()
            new_user.ModifiedBy = adminId
            new_user.ModifiedAt = datetime.now()
            try:
                db.session.add(new_user)
                db.session.commit()
                return {"Status": 1, "Description": None, "ResponseData": None}
            except Exception as ex:
                db.session.rollback()
                raise ProjectException(
                    f"DB cant finish process. Exception{ex.args}/{ex.__str__()}"
                )
        app.logger.error(
            f"Đăng ký tài khoản không thành công. Tài khoản {email} đã tồn tại"
        )
        return {
            "Status": 0,
            "Description": f"Đăng ký tài khoản không thành công. Tài khoản {email} đã tồn tại",
            "ResponseData": None,
        }
    except ProjectException as pEx:
        app.logger.exception(f"register thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Đăng ký không thành công",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"register thất bại. Có exception[{ex}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Đăng ký tài khoản không thành công",
            "ResponseData": None,
        }, 200
    finally:
        pass


# GET api/auth/login
@Authentication.route("/login", methods=["POST"])
def login():
    try:
        jsonRequestData = request.get_json()
        email = None if "email" not in jsonRequestData else jsonRequestData["email"]
        password = (
            None if "password" not in jsonRequestData else jsonRequestData["password"]
        )

        # region validate

        if not email or not isinstance(email, str) or not email.strip():
            raise ProjectException(
                "Email không hợp lệ."
            )
        if not password or not isinstance(password, str) or not password.strip():
            raise ProjectException(
                "Mật khẩu không hợp lệ"
            )

        # endregion

        exist = (
            db.session.query(UserModel)
            .where(or_(UserModel.EmailAddress == email, UserModel.Username == email))
            .first()
        )
        if not exist:
            app.logger.error(
                f"login không thành công thành công tài khoản. Tài khoản {email} chưa đăng ký!"
            )
            return {
                "Status": 0,
                "Description": f"Tài khoản chưa đăng ký!",
                "ResponseData": None,
            }, 200

        if not exist.verify_password(password):
            app.logger.error(
                f"login không thành công thành công tài khoản. Tài khoản {email} chưa đăng ký!"
            )
            return {
                "Status": 0,
                "Description": f"Tài khoản hoặc mật khẩu chưa đúng!",
                "ResponseData": None,
            }, 200
        identity = {"email": exist.EmailAddress, "username": exist.Username}
        access_token = create_access_token(
            identity=identity,
            additional_claims={
                "id": exist.Id,
                "username": exist.Username,
                "email": exist.EmailAddress,
                "IsAdmin": True if exist.Role == 1 else False,
            },
        )
        app.logger.info(f"login thành công tài khoản {email}.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"access_token": access_token},
        }, 200
            
    except ProjectException as pEx:
        app.logger.error(f"login thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Đăng nhập không thành công. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.error(f"login thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Đăng nhập tài khoản không thành công",
            "ResponseData": None,
        }, 200
    finally:
        pass


@Authentication.route("/request/reset-password", methods=["GET"])
def request_reset_password():
    try:
        clientUrl = request.origin
        email = request.args.get("email")

        # region validate

        if not isinstance(email, str) or not email or not email.strip():
            raise ProjectException(
                "Invalid email. Email is empty or blank or not string"
            )
        emailRegex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(emailRegex, email):
            raise ProjectException(f"Email {email} is not an valid email.")

        # endregion

        exist = UserModel.query.filter(UserModel.EmailAddress == email).first()
        if not exist:
            raise ProjectException(f"Email {email} chưa được đăng ký.")
        identity = {"email": email, "username": exist.Username}
        additional_claims = {
            "id": exist.Id,
            "username": exist.Username,
            "email": email,
            "IsAdmin": True if exist.Role == 1 else False,
        }
        reset_link = urljoin(
            base=str(clientUrl),
            url=f"/reset-password/{create_access_token(identity=identity, additional_claims=additional_claims)}",
        )
        send_email(
            subject="Reset password",
            html_body=render_template(
                "reset_password.html", receiver=exist.Username, reset_link=reset_link
            ),
            recipients=[email],
            sender="admin",
            text_body="",
        )
        print("clientUrl", clientUrl)
        print("reset_link", reset_link)
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200
    except ProjectException as pEx:
        app.logger.exception(f"request_reset_password có lỗi. {pEx}")
        return {
            "Status": 0,
            "Description": f"Yêu cầu không thành công. {pEx}",
            "ResponseData": None,
        }
    except Exception as ex:
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. \nKhông thể thay đổi mật khẩu",
            "ResponseData": None,
        }, 200
    finally:
        pass


@Authentication.route("/reset_password", methods=["POST"])
@jwt_required(locations="json")
def reset_password():
    jsonRequestData = request.get_json()
    new_password = jsonRequestData["new_password"]
    jti = get_jwt()["jti"]
    try:
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        existUser = UserModel.query.filter(and_(UserModel.EmailAddress == email, UserModel.Username == username)).first()
        if not existUser:
            raise Exception(f"Could not find user {email}")
        # existUser.PasswordHash = bcrypt.generate_password_hash(new_password).decode(
        #     "utf-8"
        # )
        existUser.password = new_password
        existUser.ModifiedAt = datetime.now()
        existUser.ModifiedBy = existUser.Id
        db.session.add(TokenBlockList(jti=jti, created_at=datetime.now()))
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Failed to reset password.",
            "ResponseData": None,
        }, 200
    finally:
        pass


@Authentication.route("/logout", methods=["POST"])
@jwt_required()  # require Header of req Authorization: Bearer <access_token>
def logout():
    try:
        jti = get_jwt()["jti"]
        db.session.add(TokenBlockList(jti=jti, created_at=datetime.now()))
        db.session.commit()
        return {
            "Status": 1,
            "Description": "Logged out",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": "Logged out fail.",
            "ResponseData": None,
        }, 200
    finally:
        pass


# POST api/auth/changepwd
@Authentication.route("/changepwd", methods=["POST", "PUT"])
@jwt_required()
def changePassword():
    try:
        jsonRequestData = request.get_json()
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        password = (
            None if "Password" not in jsonRequestData else jsonRequestData["Password"]
        )

        NewPassword = (
            None
            if "NewPassword" not in jsonRequestData
            else jsonRequestData["NewPassword"]
        )

        ConfirmPassword = (
            None if "Confirm" not in jsonRequestData else jsonRequestData["Confirm"]
        )

        # region validation

        if not password:
            raise Exception(f"Mật khẩu không hợp lệ")
        if not NewPassword:
            raise Exception(f"Mật khẩu mới không hợp lệ")
        if not ConfirmPassword:
            raise Exception(f"Nhập lại mật khẩu không hợp lệ")

        # endregion

        currentUser = UserModel.query.filter(
            and_(UserModel.EmailAddress == email, UserModel.Username == username)
        ).first()
        if not currentUser:
            app.logger.error(
                f"changePassword thất bại. Không tìm thấy người dùng {username} - {email}"
            )
            return {
                "Status": 2,  # không tìm thấy user
                "Description": f"Không tìm thấy người dùng {username} - {email}",
                "ResponseData": None,
            }, 200
        # if not bcrypt.check_password_hash(currentUser.PasswordHash, password):
        #     raise ProjectException("Mật khẩu vừa nhập không đúng.")
        if not currentUser.verify_password(password):
            raise ProjectException("Mật khẩu vừa nhập không đúng.")
        # currentUser.PasswordHash = bcrypt.generate_password_hash(NewPassword)
        currentUser.password = NewPassword
        db.session.commit()
        app.logger.info(f"Đổi mật khẩu cho user [{username}] thành công")
        return {
            "Status": 1,
            "Description": f"Đổi mật khẩu thành công.",
            "ResponseData": None,
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.error(f"changePassword thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Đổi mật khẩu không thành công. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.error(f"changePassword thất bại. Có exception[{ex}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Đổi mật khẩu tài khoản không thành công",
            "ResponseData": None,
        }, 200
    finally:
        pass
