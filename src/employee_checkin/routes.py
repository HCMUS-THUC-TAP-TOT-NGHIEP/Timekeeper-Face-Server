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
from sqlalchemy import and_, case, delete, func, insert, or_, select, DateTime, between
from src.shift.model import ShiftAssignment, ShiftAssignmentDetail, ShiftModel, ShiftAssignmentType, TargetType, ShiftDetailModel, ShiftDetailSchema, vShiftDetail, DayInWeekEnum

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


# GET "api/checkin/list"
@EmployeeCheckinRoute.route("/list/v2", methods=["POST"])
@jwt_required()
def getCheckinRecordV2():
    app.logger.info(f"getCheckinRecord v2 bắt đầu")
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
        Page = (jsonRequestData["Page"]
                  if "Page" in jsonRequestData else 1)
        PageSize = (jsonRequestData["PageSize"]
                  if "PageSize" in jsonRequestData else 50)
        result = AttendanceStatistic.QueryManyV2(
            DateFrom=DateFrom, DateTo=DateTo, Keyword=Keyword, Page=Page, PageSize=PageSize)
        # data = AttendanceStatisticSchema(many=True).dump(result)
        count = result.total
        data = AttendanceStatisticSchema(many=True).dump(result.items)

        # dataList = list(map(lambda key: dataDict[key], dataDict.keys()))
        app.logger.info(f"getCheckinRecord v2 thành công")
        return {
            "Status": 1,
            "Description": f"",
            "ResponseData": {
                "Statistics": data,
                "Total": count
            },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"getCheckinRecord v2 thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"getCheckinRecord v2 thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getCheckinRecord v2 kết thúc")

# PUT  "api/checkin/summary"
@EmployeeCheckinRoute.route("/summary", methods=["POST"])
@jwt_required()
def summary():
    app.logger.info(f"summary bắt đầu")
    try:
        jsonRequestData = request.get_json()
        Keyword = (
        jsonRequestData["Keyword"] if "Keyword" in jsonRequestData else None)
        DateFrom = (jsonRequestData["DateFrom"]
                    if "DateFrom" in jsonRequestData else None)
        DateTo = (jsonRequestData["DateTo"]
                  if "DateTo" in jsonRequestData else None)
        result = AttendanceStatistic.QueryMany(
            DateFrom=DateFrom, DateTo=DateTo, Keyword=Keyword)
        checkinRecord = AttendanceStatisticSchema(many=True).dump(result)
        # region Lấy các ca làm việc trong khoảng thời gian
        
        # query = db.select(ShiftModel, ShiftDetailModel.Id.label("ShiftDetailId")).select_from(ShiftModel).join(ShiftDetailModel, and_(ShiftDetailModel.ShiftId == ShiftModel.Id, or_(ShiftDetailModel.StartDate.between(DateFrom, DateTo), ShiftDetailModel.EndDate.between(
        #     DateFrom, DateTo), between(DateFrom, ShiftDetailModel.StartDate, ShiftDetailModel.EndDate), between(DateTo, ShiftDetailModel.StartDate, ShiftDetailModel.EndDate)))).where(ShiftModel.Status == 1)
        query = select(vShiftDetail).where(
            or_(vShiftDetail.StartDate.between(DateFrom, DateTo), vShiftDetail.EndDate.between(
            DateFrom, DateTo), between(DateFrom, vShiftDetail.StartDate, vShiftDetail.EndDate), between(DateTo, vShiftDetail.StartDate, vShiftDetail.EndDate))
        )
        #print(query)

        #endregion

        vShiftDetailList = db.session.execute(query).scalars().all()
        
        checkinList = AttendanceStatistic.QueryMany(DateFrom=DateFrom, DateTo=DateTo, Keyword=Keyword)

        shiftDetailList = ShiftDetailModel.query.filter_by(Status=1).all()
        app.logger.info(f"summary thành công")

        return {
            "Status": 1,
            "Description": f"",
            "ResponseData": {
                # "ShiftList": [shift.__dict__ for shift in shiftList]
            },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"summary thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"summary thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"summary kết thúc")
