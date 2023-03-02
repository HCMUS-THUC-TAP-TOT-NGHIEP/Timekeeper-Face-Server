from flask import Blueprint, jsonify, current_app as app
from src.jwt import (
    jwt_required,
    get_jwt_identity,
)
from src import cross_origin

User = Blueprint("user", __name__)


# GET api/user
@User.route("", methods=["GET"])
@jwt_required()
def authorization():
    try:
        email = get_jwt_identity()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"email": email},
        }
    except Exception as ex:
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Failed to reset password.",
            "ResponseData": None,
        }
