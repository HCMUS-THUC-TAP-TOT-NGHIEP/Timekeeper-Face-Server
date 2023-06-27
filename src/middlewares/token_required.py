from functools import wraps

from flask import Flask
from flask import current_app as app
from flask import jsonify

from src.authentication.model import UserModel
from src.db import db
from src.jwt import (JWTManager, create_access_token, get_jwt, jwt,
                     verify_jwt_in_request)


def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            result = verify_jwt_in_request(True)
            if not result:
                app.logger.error("admin_required() Tài khoản không có quyền truy cập do không tìm thấy token.")
                return ( jsonify(
                        Status=-1,
                        Description="Tài khoản không có quyền truy cập.",
                        ResponseData=None,
                    ), 401)
            claims = get_jwt()
            id = claims["id"]
            user = UserModel.query.filter_by(Id=id).first()
            if not user:
                app.logger.error("admin_required() Tài khoản không tồn tại.")
                return ( jsonify(
                        Status=-1,
                        Description="Tài khoản không tồn tại.",
                        ResponseData=None,
                    ), 401)
            if user.Role != 1:
                app.logger.error("admin_required() Tài khoản không có quyền truy cập do không phải admin")
                return (
                    jsonify(
                        Status=-1,
                        Description="Yêu cầu tài khoản có quyền quản trị viên",
                        ResponseData=None,
                    ), 401
                )
            return fn(*args, **kwargs)
        return decorator
    return wrapper

def admin_hrm_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            result = verify_jwt_in_request(True)
            if not result:
                app.logger.error("admin_required() Tài khoản không có quyền truy cập do không tìm thấy token.")
                return ( jsonify(
                        Status=-1,
                        Description="Tài khoản không có quyền truy cập.",
                        ResponseData=None,
                    ), 401)
            claims = get_jwt()
            id = claims["id"]
            user = UserModel.query.filter_by(Id=id).first()
            if not user:
                app.logger.error("admin_required() Tài khoản không tồn tại.")
                return ( jsonify(
                        Status=-1,
                        Description="Tài khoản không tồn tại.",
                        ResponseData=None,
                    ), 401)
            if user.Role != 2 and user.Role != 1:
                app.logger.error("admin_required() Tài khoản không có quyền truy cập do không phải admin")
                return (
                    jsonify(
                        Status=-1,
                        Description="Yêu cầu tài khoản có quyền quản trị nhân sự",
                        ResponseData=None,
                    ), 401
                )
            return fn(*args, **kwargs)
        return decorator
    return wrapper
