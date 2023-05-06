from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request

from src.authentication.model import UserModel
from src.db import db
from src.employee.model import (EmployeeModel, employeeInfoListSchema,
                                employeeInfoSchema)
from src.employee_checkin.model import EmployeeCheckin, employeeCheckinListSchema
from src.extension import ProjectException
from src.jwt import get_jwt_identity, jwt_required, get_jwt
from src.middlewares.token_required import admin_required
from sqlalchemy import and_, case, delete, func, insert, or_, select, DateTime

EmployeeCheckinRoute = Blueprint("/checkin", __name__)

# POST "api/checkin"


@EmployeeCheckinRoute.route("/", methods=["POST"])
@jwt_required()
def createCheckinRecord():
    try:

        pass
    except ProjectException as pEx:
        pass
    except Exception as ex:
        pass


# GET "api/checkin/list"
@EmployeeCheckinRoute.route("/list", methods=["POST"])
@jwt_required()
def getCheckinRecord():
    app.logger.info(f"getCheckinRecord bắt đầu")
    try:
        claims = get_jwt()
        id = claims["id"]
        jsonRequestData = request.get_json()
        EmployeeName = (
            jsonRequestData["EmployeeName"] if "EmployeeName" in jsonRequestData else None)
        DateFrom = (jsonRequestData["DateFrom"]
                    if "DateFrom" in jsonRequestData else None)
        DateTo = (jsonRequestData["DateTo"]
                  if "DateTo" in jsonRequestData else None)

        print(DateFrom, DateTo, EmployeeName)
        print(datetime.strptime(DateFrom, '%d - %m - %Y'))
        print(datetime.strptime(DateTo, '%d - %m - %Y'))

        data = db.session.execute(
            select(func.max(EmployeeModel.Id).label("Id"), EmployeeModel.FirstName, func.min(EmployeeCheckin.Time).label(
                "FirstCheckin"), func.max(EmployeeCheckin.Time).label("LastCheckin"), func.count())
            .select_from(EmployeeModel)
            .join(EmployeeCheckin,
                  and_(EmployeeModel.Id == EmployeeCheckin.EmployeeId,
                       EmployeeCheckin.Time >= datetime.strptime(
                           DateFrom, '%d - %m - %Y'),
                       EmployeeCheckin.Time <= datetime.strptime(DateTo, '%d - %m - %Y')),
                  isouter=True)
            .group_by(EmployeeModel.Id, func.date(EmployeeCheckin.Time))
        )
        print(
            select(EmployeeModel.FirstName, EmployeeModel.LastName,
                   EmployeeModel.Id, func.min(EmployeeCheckin.Time).label("FirstCheckin"), func.max(EmployeeCheckin.Time).label("LastCheckin"))
            .select_from(EmployeeModel)
            .join(EmployeeCheckin,
                  and_(EmployeeModel.Id == EmployeeCheckin.EmployeeId,
                       EmployeeCheckin.Time >= datetime.strptime(
                           DateFrom, '%d - %m - %Y'),
                       EmployeeCheckin.Time <= datetime.strptime(DateTo, '%d - %m - %Y')),
                  isouter=True)
            .group_by(EmployeeModel.Id, func.date(EmployeeCheckin.Time))
        )
        return {
            "Status": 0,
            "Description": f"",
            "ResponseData": {
                "Statistics": [dict(r) for r in data]
            },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"getCheckinRecord thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"getCheckinRecord thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getCheckinRecord kết thúc")


# PUT "api/checkin"
@EmployeeCheckinRoute.route("/", methods=["PUT"])
@jwt_required()
def EditCheckinRecord():
    try:
        pass
    except ProjectException as pEx:
        pass
    except Exception as ex:
        pass
