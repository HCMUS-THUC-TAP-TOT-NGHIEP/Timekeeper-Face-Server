from flask import Blueprint, jsonify, render_template, request, current_app as app
from src.email import send_email
import uuid
from urllib.parse import urljoin
from datetime import datetime
from src.authentication.model import UserModel, UserSchema
from src.db import db
from src.jwt import jwt, create_access_token
import re
# from flask_jwt_extended import JWTManager, jwt_required, create_access_token

Authentication = Blueprint("auth", __name__)

userSchema = UserSchema()


# GET api/auth/register
@Authentication.route("/register", methods=["POST"])
def register():
    jsonRequestData = request.get_json()
    email = jsonRequestData["email"]
    password = jsonRequestData["password"]
    adminId = int(jsonRequestData["adminId"])
    users = UserModel.query.all()
    if len(users) == 0:
        hashedPassword = bcrypt.generate_password_hash(password)
        new_user = UserModel(
            email, hashedPassword, "", 1, status=1, role=1
        )  # role = 1 => admin
        db.session.add(new_user)
        db.session.commit()
        return {"Status": 1, "Description": None, "ResponseData": None}
    exist = UserModel.query.filter(UserModel.EmailAddress == email).first()
    if not exist:
        try:
            role = int(jsonRequestData["role"])
            hashedPassword = bcrypt.generate_password_hash(password)
            new_user = UserModel(email, hashedPassword, "", 1, status=1, role=role)
            new_user.CreatedAt = datetime.now()
            new_user.CreatedBy = adminId
            new_user.ModifiedBy = adminId
            new_user.ModifiedAt = datetime.now()
            db.session.add(new_user)
            db.session.commit()
            return {"Status": 1, "Description": None, "ResponseData": None}
        except Exception as ex:
            db.session.rollback()
            return {
                "Status": 0,
                "Description": f"Đăng ký tài khoản không thành công. Có lỗi {ex.args}/{ex.__str__()}",
                "ResponseData": None,
            }
    return {
        "Status": 0,
        "Description": f"Đăng ký tài khoản không thành công. Tài khoản {email} đã tồn tại",
        "ResponseData": None,
    }


# GET api/auth/login
@Authentication.route("/login", methods=["POST"])
def login():
    return jsonify({"data": "login"})


@Authentication.route("/request/reset-password", methods=["GET"])
def request_reset_password():
    try:
        clientUrl = app.config["FE_URL"]
        email = request.args.get("email")

        # region validate

        emailRegex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
        if not re.fullmatch(emailRegex, email):
            raise Exception(f"Email {email} is not an valid email.")

        # endregion

        exist = UserModel.query.filter(UserModel.EmailAddress == email).first()
        if not exist:
            raise Exception(f"Email {email} has been not register yet.")
        reset_link = urljoin(clientUrl, "/reset-password") + f"?token={create_access_token(identity=email)}"
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
        }
    except Exception as ex:
        app.logger.exception(ex)
        print("Failed to reset password")
        print(f"Ex: {ex.args}")
        return {
            "Status": 0,
            "Description": f"Failed to reset password.",
            "ResponseData": None,
        }
    finally:
        pass


@Authentication.route("/reset_password", methods=["GET"])
def reset_password():
    token = request.args.get("token")
    return token
