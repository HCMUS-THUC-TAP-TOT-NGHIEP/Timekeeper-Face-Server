from flask import Blueprint, jsonify, render_template, request, current_app
from src.email import send_email
import uuid
from urllib.parse import urljoin
from datetime import datetime
from src.authentication.model import UserModel, UserSchema
from src.db import db
from src import bcrypt
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
            new_user = UserModel(
                email, hashedPassword, "", 1, status=1, role=role
            )
            new_user.CreatedAt = datetime.now()
            new_user.CreatedBy = adminId
            new_user.ModifiedBy = adminId
            new_user.ModifiedAt = datetime.now()
            db.session.add(new_user)
            db.session.commit()
            return {"Status": 1, "Description": None, "ResponseData": None}
        except Exception as ex:
            db.session.rollback()
            return {"Status": 0, "Description": f'Đăng ký tài khoản không thành công. Có lỗi {ex.args}/{ex.__str__()}', "ResponseData": None}
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
    receiver = request.args.get("email")
    reset_link = (
        urljoin(current_app.config["FE_URL"], "/reset-password")
        + f"?token={uuid.uuid4()}"
    )
    send_email(
        subject="Reset password",
        html_body=render_template(
            "test_email.html", receiver=receiver, reset_link=reset_link
        ),
        recipients=[receiver],
        sender="admin@gmail.com",
        text_body="",
    )
    return reset_link


@Authentication.route("/reset_password", methods=["GET"])
def reset_password():
    token = request.args.get("token")
    return token
