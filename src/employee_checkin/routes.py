from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request

from src.authentication.model import UserModel
from src.db import db
from src.employee.model import (EmployeeModel, employeeInfoListSchema,
                                employeeInfoSchema)
from src.employee_checkin.EmployeeCheckin import EmployeeCheckin, employeeCheckinListSchema
from src.employee_checkin.AttendanceStatistic import AttendanceStatistic, AttendanceStatisticSchema
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
        Keyword = (
            jsonRequestData["Keyword"] if "Keyword" in jsonRequestData else None)
        DateFrom = (jsonRequestData["DateFrom"]
                    if "DateFrom" in jsonRequestData else None)
        DateTo = (jsonRequestData["DateTo"]
                  if "DateTo" in jsonRequestData else None)
        result = AttendanceStatistic.QueryMany(
            DateFrom=DateFrom, DateTo=DateTo, Keyword=Keyword)
        data = AttendanceStatisticSchema(many=True).dump(result)
        dataDict = dict()
        for d in data:
            if d["Id"] not in dataDict.keys():
                dataDict[d["Id"]] = {
                    "Id": d["Id"],
                    "EmployeeName": d["EmployeeName"],
                    "CheckinList": {}
                }
            dataDict[d["Id"]]["CheckinList"][d["Date"]] = {
                "FirstCheckin": d["FirstCheckin"].split("T")[1],
                "LastCheckin": d["LastCheckin"].split("T")[1]
            }

        dataList = list(map(lambda key: dataDict[key], dataDict.keys()))
        app.logger.info(f"getCheckinRecord thành công")
        return {
            "Status": 1,
            "Description": f"",
            "ResponseData": {
                "Statistics": dataList,
                "Total": dataDict.__len__()
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
