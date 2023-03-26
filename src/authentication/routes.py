import re
from datetime import datetime
from urllib.parse import urljoin

from flask import Blueprint
from flask import current_app as app
from flask import render_template, request

from src import bcrypt
from src.authentication.model import UserModel, UserSchema
from src.db import db
from src.email import send_email
from src.extension import ProjectException
from src.jwt import (
    TokenBlocklist,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import select, or_

Authentication = Blueprint("auth", __name__)

userSchema = UserSchema()


# GET api/auth/register
@Authentication.route("/register", methods=["POST"])
def register():
    try:
        jsonRequestData = request.get_json()
        email = jsonRequestData["email"]
        password = jsonRequestData["password"]
        # region validate

        if not isinstance(email, str) or not email or not email.strip():
            raise ProjectException(
                "Invalid email. Email is empty or blank or not string"
            )
        emailRegex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(emailRegex, email):
            raise ProjectException(f"Email {email} is not an valid email.")
        if not isinstance(password, str) or not password or not password.strip():
            raise ProjectException(
                "Invalid password. Password empty or blank or not string"
            )

        # endregion

        users = UserModel.query.all()
        if len(users) == 0:
            hashedPassword = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = UserModel(
                email, hashedPassword, "", 1, status=1, role=1
            )  # role = 1 => admin
            db.session.add(new_user)
            db.session.commit()
            return {"Status": 1, "Description": None, "ResponseData": None}
        exist = UserModel.query.filter(UserModel.EmailAddress == email).first()
        if not exist:
            if not isinstance(jsonRequestData["adminId"], str):
                raise Exception("Admin ID is not valid")
            if not isinstance(jsonRequestData["role"], str):
                raise Exception("Role is not valid")
            role = int(jsonRequestData["role"])
            adminId = int(jsonRequestData["adminId"])
            hashedPassword = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = UserModel(email, hashedPassword, "", 1, status=1, role=role)
            new_user.CreatedAt = datetime.now()
            new_user.CreatedBy = adminId
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
        app.logger.exception(f"register thất bại. Có exception[{str(ex)}]")
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

        if not isinstance(email, str) or not email or not email.strip():
            raise ProjectException(
                "Invalid email. Email is empty or blank or not string"
            )
        if not isinstance(password, str) or not password or not password.strip():
            raise ProjectException(
                "Invalid password. Password empty or blank or not string"
            )

        # endregion

        exist = (
            db.session.query(UserModel)
            .where(or_(UserModel.EmailAddress == email, UserModel.Username == email))
            .first()
        )
        if exist:
            if bcrypt.check_password_hash(exist.PasswordHash, password):
                identity = {"email": email, "username": exist.Username}
                access_token = create_access_token(
                    identity=identity,
                    additional_claims={
                        "id": exist.Id,
                        "username": exist.Username,
                        "email": email,
                        "IsAdmin": True if exist.Role == 1 else False,
                    },
                )
                app.logger.info(f"login thành công tài khoản {email}.")
                return {
                    "Status": 1,
                    "Description": None,
                    "ResponseData": {"access_token": access_token},
                }, 200
        app.logger.error(
            f"login không thành công thành công tài khoản. Tài khoản {email} chưa đăng ký!"
        )
        return {
            "Status": 0,
            "Description": f"Tài khoản chưa đăng ký!",
            "ResponseData": None,
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
        clientUrl = app.config["CLIENT_URL"]
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
        additional_claims = (
            {
                "id": exist.Id,
                "username": exist.Username,
                "email": email,
                "IsAdmin": True if exist.Role == 1 else False,
            },
        )
        reset_link = urljoin(
            clientUrl,
            f"/reset-password/{create_access_token(identity=identity, additional_claims=additional_claims)}",
        )
        send_email(
            subject="Reset password",
            html_body=render_template(
                "reset_password.html", receiver=email, reset_link=reset_link
            ),
            recipients=[email],
            sender="admin@gmail.com",
            text_body="",
        )
        return {
            "Status": 1,
            "Description": f"Check mail",
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
        print("Failed to reset password")
        print(f"Ex: {ex.args}")
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
        existUser = UserModel.query.filter(UserModel.EmailAddress == email).first()
        if not existUser:
            raise Exception(f"Could not find user {email}")
        existUser.PasswordHash = bcrypt.generate_password_hash(new_password).decode(
            "utf-8"
        )
        existUser.ModifiedAt = datetime.now()
        existUser.ModifiedBy = existUser.Id
        db.session.add(TokenBlocklist(jti=jti, created_at=datetime.now()))
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
        db.session.add(TokenBlocklist(jti=jti, created_at=datetime.now()))
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
