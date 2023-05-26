from functools import wraps

from flask import Flask, jsonify
from src.jwt import (
    jwt,
    JWTManager,
    create_access_token,
    get_jwt,
    verify_jwt_in_request,
)

def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims["IsAdmin"]:
                return fn(*args, **kwargs)
            else:
                return (
                    jsonify(
                        Status=0,
                        Description="Yêu cầu tài khoản có quyền quản trị viên",
                        ResponseData=None,
                    ), 200
                )
        return decorator
    return wrapper
