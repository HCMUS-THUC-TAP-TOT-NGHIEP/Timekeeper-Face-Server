from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt_identity,
    verify_jwt_in_request,
    get_jwt,
)
from functools import wraps
from flask import jsonify
from src.db import db
from sqlalchemy import Column, Integer, String, DateTime


jwt = JWTManager()
blacklist = set()


class TokenBlocklist(db.Model):
    __tablename__ = "TokenBlock"

    id = Column(Integer(), primary_key=True)
    jti = Column(String(), nullable=False, index=True)
    created_at = Column(DateTime(), nullable=False)


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None


def admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            # if claims["is_administrator"]:
            #     return fn(*args, **kwargs)
            if claims["email"]:
                return fn(*args, **kwargs)
            else:
                return {
                    "Status": -1,
                    "Description": f"Token has expired",
                    "ResponseData": None,
                }, 403

        return decorator

    return wrapper
