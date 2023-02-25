from flask import Blueprint, jsonify, render_template, request, current_app
from src.email import send_email
import uuid
import os
from urllib.parse import urljoin
Authentication = Blueprint("auth", __name__, static_folder="public", template_folder="templates")


# GET api/auth/register
@Authentication.route("/register", methods=["POST"])
def register():
    return jsonify({"data": "register"})


# GET api/auth/login
@Authentication.route("/login", methods=["POST"])
def login():
    return jsonify({"data": "login"})

@Authentication.route("/request/reset-password", methods=["GET"])
def request_reset_password():
    receiver = request.args.get("email")
    # print(os.path.join(current_app.root_path, "templates", "test_email.html"))
    # return os.path.join(current_app.root_path, "templates", "test_email.html")
    # return render_template("test_email.html")
    reset_link = urljoin(current_app.config["FE_URL"], "/reset-password")+ f"?token={uuid.uuid4()}"
    send_email(
        subject="Reset password",
        html_body = render_template("test_email.html", receiver=receiver, reset_link=reset_link),
        recipients= [receiver],     
        sender='admin@gmail.com',
        text_body=''
    )
    return reset_link

@Authentication.route("/reset_password", methods=["GET"])
def reset_password():
    token = request.args.get("token")
    return token