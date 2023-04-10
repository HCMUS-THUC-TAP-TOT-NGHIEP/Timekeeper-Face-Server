from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request

from src.authentication.model import UserModel
from src.db import db
from src.employee.model import (EmployeeModel, employeeInfoListSchema,
                                employeeInfoSchema)
from src.extension import ProjectException
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required

EmployeeCheckin = Blueprint("/checkin", __name__)

# POST "api/checkin"
EmployeeCheckin.route("/", methods=["POST"])
@jwt_required()
def createCheckinRecord():
    try:
        pass
    except ProjectException as pEx:
        pass
    except Exception as ex:
        pass

# GET "api/checkin"
EmployeeCheckin.route("/", methods=["GET"])
@jwt_required()
def getCheckinRecord():
    try:
        pass
    except ProjectException as pEx:
        pass
    except Exception as ex:
        pass

# PUT "api/checkin"
EmployeeCheckin.route("/", methods=["PUT"])
@jwt_required()
def getCheckinRecord():
    try:
        pass
    except ProjectException as pEx:
        pass
    except Exception as ex:
        pass
