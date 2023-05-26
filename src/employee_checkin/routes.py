from datetime import date, datetime, timedelta

from flask import Blueprint
from flask import current_app as app
from flask import request, send_from_directory
from sqlalchemy import (DateTime, and_, between, case, delete, func, insert,
                        or_, select)

from src.authentication.model import UserModel
from src.config import Config
from src.db import db
from src.employee.model import (EmployeeModel, employeeInfoListSchema,
                                employeeInfoSchema)
from src.employee_checkin.AttendanceStatistic import (
    AttendanceStatistic, AttendanceStatisticSchema, AttendanceStatisticV2)
from src.employee_checkin.EmployeeCheckin import (EmployeeCheckin,
                                                  employeeCheckinListSchema)
from src.employee_checkin.Timesheet import (Timesheet, TimesheetDetail,
                                            TimesheetDetailSchema,
                                            timesheetDetailListSchema,
                                            timesheetDetailSchema,
                                            timesheetListSchema,
                                            timesheetSchema)
from src.extension import ProjectException
from src.jwt import get_jwt, get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.shift.model import (DayInWeekEnum, ShiftAssignment,
                             ShiftAssignmentDetail, ShiftAssignmentType,
                             TargetType)
from src.shift.ShiftModel import (ShiftDetailModel, ShiftDetailSchema,
                                  ShiftModel, vShiftDetail, vShiftDetailSchema)

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
        result = AttendanceStatisticV2.QueryMany(
            DateFrom=DateFrom, DateTo=DateTo, Keyword=Keyword, Page=Page, PageSize=PageSize)
        count = result.total
        data = AttendanceStatisticSchema(many=True).dump(result.items)
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

#GET api/checkin/import/templates
@EmployeeCheckinRoute.route("/timekeeper/templates", methods=["GET", "POST"])
@admin_required()
def GetTemplate():
    try:
        app.logger.info("GetTemplate timekeeper bắt đầu")
        claims = get_jwt()
        id = claims['id']
        params = request.args
        FileName = params['FileName']
        excelTemplatePath = Config.EXCELTEMPLATEPATH
        if FileName == "TimekeeperDataTemplate":
            return send_from_directory(excelTemplatePath, "TimekeeperDataTemplate.xlsx", as_attachment=True)
        else:
            raise ProjectException("Không tìm thấy tệp tin mẫu.")

    except ProjectException as ex:
        db.session.rollback()
        app.logger.info(
            f"Importing timekeeper thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"{ex}",
            "ResponseData": None,
        }, 400
    except Exception as ex:
        db.session.rollback()
        app.logger.info(
            f"GetTemplate timekeeper thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 400
    finally:
        app.logger.info("GetTemplate timekeeper kết thúc")

# GET api/checkin/timesheet
@EmployeeCheckinRoute.route("/timesheet", methods=["GET"])
@admin_required()
def getTimeSheetList():
    try:
        app.logger.info(f"getTimeSheetList bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        requestData = request.args
        Keyword = (
            requestData["Keyword"] if "Keyword" in requestData else None)
        Page = int(requestData["Page"]
                  if "Page" in requestData else 1)
        PageSize = int(requestData["PageSize"]
                  if "PageSize" in requestData else 50)
        result = Timesheet.QueryMany(Keyword=Keyword, Page=Page, PageSize=PageSize)
        count = result.total
        data = timesheetListSchema.dump(result.items)
        app.logger.info(f"getCheckinRecord v2 thành công")
        return {
            "Status": 1,
            "Description": f"",
            "ResponseData": {
                "TimesheetList": data,
                "Total": count
            },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"getTimeSheetList thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"getTimeSheetList thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getTimeSheetList kết thúc")

# POST api/checkin/timesheet
@EmployeeCheckinRoute.route("/timesheet", methods=["POST"])
@admin_required()
def createTimeSheet():
    try:
        app.logger.info(f"getTimeSheetList bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        jsonRequestData = request.get_json()
        Name = (
            jsonRequestData["Name"] if "Name" in jsonRequestData else None)
        DateFrom = (jsonRequestData["DateFrom"]
                  if "DateFrom" in jsonRequestData else None)
        DateTo = (jsonRequestData["DateTo"]
                  if "DateTo" in jsonRequestData else None)
        DepartmentList = (jsonRequestData["DepartmentList"]
                  if "DepartmentList" in jsonRequestData else [])
                  
        #region validate

        if not Name or not Name.strip():
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp tên báo cáo.")
        if not DateFrom:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp ngày bắt đầu báo cáo.")
        if not DateTo:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp ngày kết thúc báo cáo.")

        #endregion

        newTimeSheet = Timesheet()
        newTimeSheet.Name = Name
        newTimeSheet.DateFrom = DateFrom
        newTimeSheet.DateTo = DateTo
        newTimeSheet.DepartmentList = DepartmentList
        newTimeSheet.LockedStatus = False
        newTimeSheet.CreatedAt = datetime.now()
        newTimeSheet.CreatedBy = id
        newTimeSheet.ModifiedAt = datetime.now()
        newTimeSheet.ModifiedBy = id
        db.session.add(newTimeSheet)
        db.session.flush()
        db.session.refresh(newTimeSheet)

        #region query: ghi lại chi tiết chấm công
        
        checkinRecordList = AttendanceStatisticV2.QueryMany(DateFrom=DateFrom, DateTo=DateTo)["items"]
        # if (len(checkinRecordList) == 0):
            # raise ProjectException("")
        query = db.select(EmployeeModel)
        if len(DepartmentList) > 0:
            query = query.where(EmployeeModel.DepartmentId.in_(DepartmentList))
        employeeList = db.session.execute(query).scalars()
            
        # employeeList = employeeInfoListSchema.dump(data)
        delta = timedelta(days=1)     
        for employee in employeeList:
            currentDate = date.fromisoformat(DateFrom)
            endDate = date.fromisoformat(DateTo)
            while currentDate <= endDate:
                timeSheetDetail = TimesheetDetail()
                times = list()
                checkinRecords = list(filter(lambda x: x.Id == employee.Id and x.Date == currentDate, checkinRecordList))
                counts = checkinRecords.__len__()
                timeSheetDetail.EmployeeId = employee.Id
                timeSheetDetail.Date = currentDate
                timeSheetDetail.CheckinTime =  checkinRecords[0].Time if counts > 0 else None
                timeSheetDetail.CheckoutTime = checkinRecords[1].Time if counts > 1 else None
                timeSheetDetail.TimesheetId = newTimeSheet.Id
                db.session.add(timeSheetDetail)
                currentDate+=delta

        # endregion
        db.session.commit()
        app.logger.info(f"getCheckinRecord v2 thành công")

        return {
            "Status": 1,
            "Description": f"",
            "ResponseData": { "Id": newTimeSheet.Id },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"getTimeSheetList thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"getTimeSheetList thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getTimeSheetList kết thúc")

# GET api/checkin/timesheet-detail
@EmployeeCheckinRoute.route("/timesheet/detail", methods=["GET"])
@admin_required()
def getTimesheetDetails():
    try:
        app.logger.info(f"getTimesheetDetails bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        requestData = request.args
        TimesheetId = (
            requestData["Id"] if "Id" in requestData else None)
        #region validate
        if not TimesheetId:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp mã báo cáo.")
        #endregion
        exist = Timesheet.query.filter_by(Id=int(TimesheetId)).first()
        if not exist:
            raise ProjectException(f"Không tìm thấy bảng phân ca mã {TimesheetId}.")
        data = exist.QueryDetails()
        detailList = TimesheetDetailSchema(many=True).dump(data)
        # detailList = []
        

        app.logger.info(f"getTimesheetDetails thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "Detail": detailList,
                "Timesheet": timesheetSchema.dump(exist),
                "Total": len(detailList)
            },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"getTimesheetDetails thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"getTimesheetDetails thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getTimesheetDetails kết thúc")
