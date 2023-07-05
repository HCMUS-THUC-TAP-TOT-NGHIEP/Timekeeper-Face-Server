import pandas
from werkzeug.utils import secure_filename
import os
from threading import Thread
import threading
from datetime import date, datetime, timedelta
from flask import Blueprint, send_file
from flask import current_app as app
from flask import request, send_from_directory
from sqlalchemy import (DateTime, and_, between, case, delete, func, insert, distinct,
                        or_, select)

from src.authentication.model import UserModel
from src.config import Config
from src.db import db
from src.employee.model import (EmployeeModel, employeeInfoListSchema,
                                employeeInfoSchema)
from src.employee_checkin.AttendanceStatistic import (
    AttendanceStatistic, AttendanceStatisticSchema, AttendanceStatisticV2)
from src.employee_checkin.EmployeeCheckin import (EmployeeCheckin,
                                                  employeeCheckinListSchema, CheckinMethodModel, CheckinMethodSchema)
from src.employee_checkin.Timesheet import (Timesheet, TimesheetDetail,
                                            TimesheetDetailSchema,
                                            timesheetDetailListSchema,
                                            timesheetDetailSchema,
                                            timesheetListSchema,
                                            timesheetSchema)
from src.utils.extension import ProjectException
from src.jwt import get_jwt, get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.shift.model import (DayInWeekEnum, ShiftAssignment,
                             ShiftAssignmentDetail, ShiftAssignmentType,
                             TargetType)
from src.shift.ShiftModel import (ShiftDetailModel, ShiftDetailSchema,
                                  ShiftModel, vShiftDetail, vShiftDetailSchema)
from src.utils.helpers import DeleteFile, daterange
from dateutil.parser import parse

EmployeeCheckinRoute = Blueprint("/checkin", __name__)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def CheckIfFileAllowed(filename):
    if ('.' not in filename):
        return False
    extension = GetFileExtensionFromFileNam(filename)
    if extension not in ALLOWED_EXTENSIONS:
        return False
    return True

def GetFileExtensionFromFileNam(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else None

# POST "api/checkin"
@EmployeeCheckinRoute.route("/new", methods=["POST"])
def createCheckinRecord():
    try:
        app.logger.info(f"createCheckinRecord bắt đầu")
        jsonRequest = request.form
        Image = jsonRequest["Image"] if "Image" in jsonRequest else ""  #base64 encoded
        Method = int(jsonRequest["Method"]) if "Method" in jsonRequest else None
        EmployeeId = int(jsonRequest["EmployeeId"]) if "EmployeeId" in jsonRequest else None
        AttendanceTime = jsonRequest["AttendanceTime"] if "AttendanceTime" in jsonRequest else None

        #region validation

        if not Image:
            raise ProjectException("Không ghi nhận chấm công do thiếu hình ảnh.")
        if not Method:
            raise ProjectException("Không ghi nhận chấm công do thiếu thông tin hình thức chấm công.")
        if not EmployeeId:
            raise ProjectException("Không ghi nhận chấm công do thiếu thông tin nhân viên.")
        exist = EmployeeModel.query.filter_by(Id=EmployeeId).first()
        if not exist:
            raise ProjectException(f"Không tìm thấy nhân viên có mã {EmployeeId}.")
        if not AttendanceTime:
            raise ProjectException(f"Chưa cung cấp thông tin giờ.")
        AttendanceTime = datetime.fromisoformat(AttendanceTime)

        #endregion

        EmployeeCheckin.InsertOne(app=app._get_current_object(),employee_id=EmployeeId, method=Method, method_text="", time=AttendanceTime, image_data=Image.split(",")[-1])
        db.session.commit()
        app.logger.info(f"createCheckinRecord thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200

    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"createCheckinRecord thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"createCheckinRecord thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"createCheckinRecord kết thúc")

# GET api/checkin/method
@EmployeeCheckinRoute.route("/method", methods=["GET"])
def GetAllCheckinMethods():
    try: 
        app.logger.info(f"GetAllCheckinMethods bắt đầu")
        result = CheckinMethodModel.query.all()
        app.logger.info(f"GetAllCheckinMethods thành công")
        return {
            "Status": 1,
            "Description": f"",
            "ResponseData": {
                "CheckinMethodList": CheckinMethodSchema(many=True).dump(result),
                "Total": len(result)
            },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"GetAllCheckinMethods thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"GetAllCheckinMethods thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"GetAllCheckinMethods kết thúc")

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
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getCheckinRecord kết thúc")

# GET "api/checkin/list/v2"
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
        MethodList = (jsonRequestData["MethodList"]
                  if "MethodList" in jsonRequestData else [])
        Page = (jsonRequestData["Page"]
                  if "Page" in jsonRequestData else 1)
        PageSize = (jsonRequestData["PageSize"]
                  if "PageSize" in jsonRequestData else 50)
        result = AttendanceStatisticV2.QueryMany(
            DateFrom=DateFrom, DateTo=DateTo, Keyword=Keyword, Page=Page, PageSize=PageSize, MethodList=MethodList)
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
            "Description": f"Xảy ra lỗi ở máy chủ.",
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
            "Description": f"Xảy ra lỗi ở máy chủ.",
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
        if not FileName:
            raise ProjectException("Yêu cầu không hợp lệ.")

        templatePath = os.path.join(
            os.pardir, app.static_folder, "templates", "Excel", f'{FileName}.xlsx')
        if not os.path.exists(templatePath):
            raise ProjectException("Không tìm thấy tệp tin mẫu.")
        return send_file(templatePath, as_attachment=True)
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
            "Description": f"Xảy ra lỗi ở máy chủ.",
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
        count = result["total"]
        data = timesheetListSchema.dump(result["items"])
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
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getTimeSheetList kết thúc")

# POST api/checkin/timesheet/detail
@EmployeeCheckinRoute.route("/timesheet/detail", methods=["PUT"])
@admin_required()
def modifyTimesheetDetail():
    try: 
        jsonRequestData = request.get_json()
        if "Id" not in jsonRequestData:
            raise ProjectException("Yêu cầu không hợp lệ, do không có Id")
        id = jsonRequestData["Id"]
        exist = TimesheetDetail.query.filter_by(Id=id).first()
        if not exist:
            raise ProjectException(f"Không tồn tại thời gian biểu có mã {Id}")
        exist.UpdateOne(jsonRequestData)
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": TimesheetDetailSchema().dump(exist),
        }, 200
    except ProjectException as pEx:
        app.logger.exception(
            f"getTimeSheetList thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"getTimeSheetList thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
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
        newTimeSheet.InsertTimesheetDetail()
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
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getTimeSheetList kết thúc")

# DELETE api/checkin/timesheet
@EmployeeCheckinRoute.route("/timesheet", methods=["DELETE"])
@admin_required()
def DeleteTimesheet():
    try:
        app.logger.info("DeleteTimesheet bắt đầu")
        jsonRequestData = request.get_json()
        if "Id" not in jsonRequestData:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp mã báo cáo.")
        TimesheetId = jsonRequestData["Id"]
        Timesheet.DeleteById(id=TimesheetId)
        app.logger.info(f"DeleteTimesheet Id[{TimesheetId}] thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "Id": TimesheetId
            },
        }, 200

    except ProjectException as project_exception:
        app.logger.exception(
            f"DeleteTimesheet thất bại. Có exception[{str(project_exception)}]")
        return {
            "Status": 0,
            "Description": f"{str(project_exception)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"DeleteTimesheet thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"DeleteTimesheet kết thúc")
    

# PUT api/checkin/timesheet
@EmployeeCheckinRoute.route("/timesheet", methods=["PUT"])
@admin_required()
def UpdateTimesheet():
    try:
        app.logger.info(f"UpdateTimesheet bắt đầu.")
        
        jsonRequestData = request.get_json()
        if "Id" not in jsonRequestData:
            raise ProjectException("Yêu cầu không hợp lệ do chưa cung cấp định danh bảng phân ca.")

        timesheetId = int(jsonRequestData["Id"])
        # region validate
        exist = Timesheet.query.filter_by(Id=timesheetId).first()
        if not exist:
            raise ProjectException(f"Không tìm thấy bảng phân ca có mã định dang {timesheetId}")
        if exist.LockedStatus:
            raise ProjectException(f"Bảng chấm công mã {self.Id} - {self.Name} không thể chỉnh sửa vì đã khóa. ")
        exist.InsertTimesheetDetail()
        db.session.commit()
        app.logger.info(f"UpdateTimesheet thành công. ")
        return {
            "Status": 1,
            "Description": f"Cập nhật bảng phân ca {exist.Name} thành công",
            "ResponseData": None,
        }, 200

        #endregion
        pass
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"UpdateTimesheet thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"UpdateTimesheet thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"UpdateTimesheet kết thúc")


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
        searchString = (
            str(requestData["SearchString"]).strip() if "SearchString" in requestData else "")

        #region validate
        if not TimesheetId:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp mã báo cáo.")
        #endregion
        exist = Timesheet.query.filter_by(Id=int(TimesheetId)).first()
        if not exist:
            raise ProjectException(f"Không tìm thấy bảng phân ca mã {TimesheetId}.")
        result = exist.QueryDetails(SearchString=searchString)
        detailList = TimesheetDetailSchema(many=True).dump(result)

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
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getTimesheetDetails kết thúc")

# POST api/checkin/timesheet/detail/report
@EmployeeCheckinRoute.route("/timesheet/detail/report", methods=["POST"])
@admin_required()
def exportTimesheetDetailReport():
    try:
        app.logger.info(f"exportTimesheetDetailReport bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        requestData = request.args
        TimesheetId = (
            requestData["Id"] if "Id" in requestData else None)
        #region validate
        if not TimesheetId:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp mã báo cáo.")
        #endregion
        exist = db.session.execute(db.select(Timesheet).where(Timesheet.Id == int(TimesheetId))).scalars().first()
        if not exist:
            raise ProjectException(f"Không tìm thấy bảng phân ca mã {TimesheetId}.")
        data = exist.QueryDetails()
        detailList = TimesheetDetailSchema(many=True).dump(data)
        app.logger.info(f"exportTimesheetDetailReport thành công")
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
            f"exportTimesheetDetailReport thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"exportTimesheetDetailReport thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"exportTimesheetDetailReport kết thúc")

# POST api/checkin/timesheet/report
@EmployeeCheckinRoute.route("/timesheet/report", methods=["POST"])
@admin_required()
def exportTimesheetReport():
    path=""
    try:
        app.logger.info(f"exportTimesheetReport bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        requestData = request.get_json()
        TimesheetId = (
            requestData["Id"] if "Id" in requestData else None)
        #region validate
        if not TimesheetId:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp mã báo cáo.")
        #endregion
        exist = db.session.execute(db.select(Timesheet).where(Timesheet.Id == int(TimesheetId))).scalars().first()
        if not exist:
            raise ProjectException(f"Không tìm thấy bảng phân ca mã {TimesheetId}.")

        path = exist.CreateTimesheetReport()      
        response = send_file(path, as_attachment=True)
        app.logger.info(f"exportTimesheetReport thành công")
        t = threading.Thread(target=DeleteFile, args=(path, datetime.now() + timedelta(seconds=60)))
        t.start()
        return response
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"exportTimesheetReport thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"exportTimesheetReport thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"getTimesheetDetails kết thúc")

# POST "api/checkin/report"
@EmployeeCheckinRoute.route("/report", methods=["POST"])
@admin_required()
def ExportCheckinReport():
    path=""
    try:
        app.logger.info(f"ExportCheckinReport bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        jRequestData = request.get_json()
        DateFrom = jRequestData["DateFrom"] if "DateFrom" in jRequestData else None
        DateTo = jRequestData["DateTo"] if "DateTo" in jRequestData else None
        Keyword = jRequestData["Keyword"] if "Keyword" in jRequestData else None


        #region validate
        if not DateFrom:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp ngày bắt đầu.")
        if not DateTo:
            raise ProjectException("Yêu cầu không hợp lệ, do chưa cung cấp ngày kết thúc.")

        #endregion
        
        path = AttendanceStatisticV2.ExportReport(DateFrom=parse(DateFrom).date(), DateTo=parse(DateTo).date(), Keyword=Keyword)       
        response = send_file(path, as_attachment=True)
        app.logger.info(f"ExportCheckinReport thành công")
        return response
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(
            f"ExportCheckinReport thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"ExportCheckinReport thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"ExportCheckinReport kết thúc")
        t = threading.Thread(target=DeleteFile, args=(path, datetime.now() + timedelta(seconds=60)))
        t.start()


# POST "api/checkin/timesheet/import"
@EmployeeCheckinRoute.route("timesheet/import", methods=["POST"])
@admin_required()
def UpdateBulkTimesheetDetailByImport():
    try:
        app.logger.info(f"UpdateBulkTimesheetDetailByImport bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        fileRequest = request.files["ImportData"]
        timesheetId = request.form.get("TimesheetId")
        
        # region validate

        if not fileRequest:
            raise ProjectException("Không tìm thấy tệp tin")
        if not timesheetId:
            raise ProjectException("Yêu cầu không hợp lệ do không cung cấp mã timesheet")
        exist = Timesheet().query.filter_by(Id=timesheetId).first()
        if not exist:
            raise ProjectException(f"Yêu cầu không hợp lệ do không tìm thấy timesheet có mã {timesheetId}")
        if not CheckIfFileAllowed(fileRequest.filename):
            raise ProjectException(
                f"Tập tin {fileRequest.filename} có định dạng không phù hợp (cần phải là {string.join(ALLOWED_EXTENSIONS)}) ")

        # endregion

        filename = secure_filename(fileRequest.filename)
        fileExtension = GetFileExtensionFromFileNam(filename)
        if fileExtension in ['xlsx', 'xls']:
            excel_data = pandas.read_excel(
                fileRequest, sheet_name="Data", header=3)
            if (excel_data.empty):
                raise ProjectException("Tệp tin không có dữ liệu.")
            rowCount = len(excel_data.index)
            colCount = len(excel_data.columns)
            for i in range(rowCount):
                employeeCode = int(excel_data.iat[i, 0])
                date = excel_data.iat[i, 3]
                shiftId = int(excel_data.iat[i, 4])
                checkinTime = excel_data.iat[i, 5]
                checkoutTime = excel_data.iat[i, 6]
                workingHour = float(excel_data.iat[i, 7])

                if not employeeCode:
                    raise ProjectException(
                        f"Ô A{i + 1} bị trống, chưa có mã nhân viên.")

                employee = EmployeeModel.query.filter_by(Id=employeeCode).first()
                if not employee:
                    raise ProjectException(f"Không tìm thấy nhân viên có mã {employeeCode}")
                if not date:
                    raise ProjectException(
                        f"Ô D{i + 1} bị trống, chưa có ngày.")
                try:
                    date = datetime.strptime(date, "%d/%m/%Y")
                except:
                    raise ProjectException(f"Ô D{i + 1} không đúng địng dạng DD/MM/YYYY")
                if not shiftId:
                    raise ProjectException(
                        f"Ô E{i + 1} bị trống, chưa mã ca.")
                if not ShiftModel.query.filter_by(Id=shiftId).first():
                    raise ProjectException(
                        f"Ca làm việc {shiftId} không tồn tại.")
                if not checkinTime:
                    raise ProjectException(
                        f"Ô F{i + 1} bị trống, chưa có ngày.")
                if not checkoutTime:
                    raise ProjectException(
                        f"Ô G{i + 3 + 1} bị trống, chưa có ngày.")
                if not workingHour:
                    raise ProjectException(
                        f"Ô H{i + 3 + 1} bị trống, chưa có sô giờ.")


                detail = db.session.execute(db.select(TimesheetDetail).where(
                    and_(TimesheetDetail.TimesheetId==timesheetId, TimesheetDetail.EmployeeId==employeeCode
                        , TimesheetDetail.Date == date, TimesheetDetail.ShiftId == shiftId
                        )
                )).scalars().first()
                if not detail:
                    shift = ShiftDetailModel.query.filter_by(ShiftId=shiftId).first()
                    detail = db.session.execute(db.select(TimesheetDetail).where(
                        and_(TimesheetDetail.TimesheetId==timesheetId, TimesheetDetail.EmployeeId==employeeCode
                            , TimesheetDetail.Date == date, TimesheetDetail.ShiftId == None
                            )
                        )).scalars().first()
                    if not detail: continue
                    detail.ShiftId = shiftId
                    detail.StartTime = shift.StartTime
                    detail.FinishTime = shift.FinishTime
                    detail.BreakAt = shift.BreakAt
                    detail.BreakEnd = shift.BreakEnd
                
                detail.CheckinTime = checkinTime
                detail.CheckoutTime = checkoutTime              
                detail.WorkingHour = workingHour      

        elif fileExtension == 'csv':
            csv_data = pandas.read_csv(fileRequest, header=0)
            raise ProjectException(f"Không hỗ trợ file có phần mở rộng .{fileExtension}")
        db.session.commit()
        app.logger.info(f"UpdateBulkTimesheetDetailByImport thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200
    except ProjectException as pEx:
        app.logger.exception(
            f"UpdateBulkTimesheetDetailByImport thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"UpdateBulkTimesheetDetailByImport thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"UpdateBulkTimesheetDetailByImport kết thúc")

# POST api/checkin
@EmployeeCheckinRoute.route("/", methods=["POST"])
def CreateCheckinRecord():
    try:
        app.logger.info(f"CreateCheckinRecord bắt đầu.")

    except ProjectException as pEx:
        app.logger.exception(
            f"CreateCheckinRecord thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"CreateCheckinRecord thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"CreateCheckinRecord kết thúc")

# POST api/checkin/late-early/count
@EmployeeCheckinRoute.route("/late-early/count", methods=["POST"])
@admin_required()
def CountLateEarly():
    try:
        app.logger.info(f"CountLateEarly bắt đầu.")
        jsonRequestData = request.get_json()
        DateFrom = datetime.fromisoformat(jsonRequestData["DateFrom"]) if "DateFrom" in jsonRequestData and jsonRequestData["DateFrom"] else None
        if DateFrom is None:
            raise Exception("Ngày không hợp lệ")
        DateTo = datetime.fromisoformat(jsonRequestData["DateTo"]) if "DateTo" in jsonRequestData and jsonRequestData["DateTo"] else None
        countList = []
        dayList = []
        if DateTo is None: 
            result = EmployeeCheckin.CountLateEarly(DateFrom)
            countList.append(result)
            dayList.append(DateFrom.day)
        else:
            for date in daterange(DateFrom, DateTo):
                result = EmployeeCheckin.CountLateEarly(date)
                countList.append(result)
                dayList.append(date.day)
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "CountList": countList,
                "DateList": dayList,
            },
        }, 200
    except ProjectException as pEx:
        app.logger.exception(
            f"CountLateEarly thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"CountLateEarly thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"CountLateEarly kết thúc")

# GET api/checkin/late-early/count
@EmployeeCheckinRoute.route("/late-early/count", methods=["GET"])
@admin_required()
def GetCountLateEarly():
    try:
        requestData = request.args
        timesheetId = int(requestData["TimesheetId"]) if requestData["TimesheetId"] else None
        if not timesheetId:
            raise ProjectException("Chưa cung cấp mã báo cáo tổng hợp chấm công")
        employeeIdList = db.session.execute(db.select(distinct(TimesheetDetail.EmployeeId)).where(TimesheetDetail.TimesheetId==timesheetId).order_by(TimesheetDetail.EmployeeId)).scalars().all()
        timesheet = Timesheet.query.filter_by(Id=timesheetId).first()
        if not timesheet:
            raise ProjectException(f"Không tìm thấy báo cáo chấm công {timesheetId}")
        responseList = []
        for employeeId in employeeIdList:
            employee = EmployeeModel.query.filter_by(Id=employeeId).first()
            if not employee: continue
            response = employeeInfoSchema.dump(employee)
            result = timesheet.CalculateEarlyLate(EmployeeId=employeeId)
            if result["CountCheckoutEarly"] + result["CountCheckinLate"] <= 0: continue
            response["LateHour"] = round(result["CheckinLateMinute"]/60, 2)
            response["EarlyHour"] = round(result["CheckoutEarlyMinute"]/60, 2)
            response["Count"] = result["CountCheckoutEarly"] + result["CountCheckinLate"]
            responseList.append(response)
        return {
            "Status": 1,
            "Description": "",
            "ResponseData": {
                "List": responseList,
                "Total": len(responseList)
            },
        }, 200
    except ProjectException as pEx:
        app.logger.exception(
            f"GetCountLateEarly thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"GetCountLateEarly thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"GetCountLateEarly kết thúc")

# POST api/checkin/off/count
@EmployeeCheckinRoute.route("/off/count", methods=["POST"])
@admin_required()
def CountOff():
    try:
        app.logger.info(f"CountOff bắt đầu.")
        jsonRequestData = request.get_json()
        DateFrom = datetime.fromisoformat(jsonRequestData["DateFrom"]) if "DateFrom" in jsonRequestData and jsonRequestData["DateFrom"] else None
        if DateFrom is None:
            raise Exception("Ngày không hợp lệ")
        DateTo = datetime.fromisoformat(jsonRequestData["DateTo"]) if "DateTo" in jsonRequestData and jsonRequestData["DateTo"] else None
        countList = []
        dayList = []
        if DateTo is None: 
            result = EmployeeCheckin.CountOff(DateFrom)
            countList.append(result)
            dayList.append(DateFrom.day)
        else:
            for date in daterange(DateFrom, DateTo):
                result = EmployeeCheckin.CountOff(date)
                countList.append(result)
                dayList.append(date.day)
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "CountList": countList,
                "DateList": dayList,
            },
        }, 200
    except ProjectException as pEx:
        app.logger.exception(
            f"CountOff thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"CountOff thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"CountOff kết thúc")


@EmployeeCheckinRoute.route("/off/statistics", methods=["GET"])
@admin_required()
def GetCountOff():
    try: 
        requestData = request.args
        timesheetId = int(requestData["TimesheetId"]) if requestData["TimesheetId"] else None
        if not timesheetId:
            raise ProjectException("Chưa cung cấp mã báo cáo tổng hợp chấm công")
        employeeIdList = db.session.execute(db.select(distinct(TimesheetDetail.EmployeeId)).where(TimesheetDetail.TimesheetId==timesheetId).order_by(TimesheetDetail.EmployeeId)).scalars().all()
        timesheet = Timesheet.query.filter_by(Id=timesheetId).first()
        if not timesheet:
            raise ProjectException(f"Không tìm thấy báo cáo chấm công {timesheetId}")
        responseList = []
        for employeeId in employeeIdList:
            employee = EmployeeModel.query.filter_by(Id=employeeId).first()
            if not employee: continue
            response = employeeInfoSchema.dump(employee)
            result = timesheet.CalculateOff(EmployeeId=employeeId)
            if result["Count"] <= 0: continue
            response["Count"] = result["Count"]
            responseList.append(response)
        return {
            "Status": 1,
            "Description": "",
            "ResponseData": {
                "List": responseList,
                "Total": len(responseList)
            },
        }, 200

    except ProjectException as pEx:
        app.logger.exception(
            f"GetCountOff thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{str(pEx)}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"GetCountOff thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"GetCountOff kết thúc")
