import time
from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request
from flask_json import json_response
from sqlalchemy import and_, case, delete, func, insert, or_, select

from src.authentication.model import UserModel
from src.db import db
from src.department.model import DepartmentModel, DepartmentSchema
from src.designation.model import Designation
from src.employee.model import EmployeeModel, EmployeeSchema
from src.utils.extension import ProjectException, object_as_dict
from src.jwt import get_jwt, get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.shift.model import (
    ShiftAssignment,
    ShiftAssignmentDetail,
    ShiftAssignmentSchema,
    ShiftAssignmentType,
    Status,
    TargetType,
    ShiftAssignmentDetailSchema,
    vShiftAssignmentDetail,
    ShiftAssignmentEmployee,
    ShiftAssignmentDepartment
)
from src.shift.ShiftModel import (
    vShiftDetail,
    ShiftDetailModel,
     vShiftDetailSchema,   
    shiftListResponseSchema,
    shiftSchema,
    shiftListSchema,
    ShiftDetailSchema,
    ShiftModel, 
    ShiftTypeModel,
    ShiftTypeModelSchema)

Shift = Blueprint("shift", __name__)

#region Ca làm việc

# GET api/shift/list
@Shift.route("/list", methods=["GET"])
@admin_required()
def GetShiftList():
    try:
        args = request.args
        page = None
        pageSize = None
        if "Page" in args:
            page = int(args["Page"])
        if "PageSize" in args:
            pageSize = int(args["PageSize"])
        data = vShiftDetail.QueryMany(Page=page, PageSize=pageSize)

        app.logger.info(f"GetShiftList thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "ShiftList": vShiftDetailSchema(many=True).dump(data["items"]),
                "Total": data["total"]
            },
        }, 200
    except ProjectException as pEx:
        app.logger.exception(f"GetShiftList thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Không tìm thấy ca làm việc nào",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"GetShiftList thất bại. {ex}")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200


# GET api/shift/type/list
@Shift.route("/type/list", methods=["GET"])
def GetShiftTypeList():
    try:
        app.logger.info("GetShiftTypeList bắt đầu")
        shiftTypeList = ShiftTypeModel.query.all()
        app.logger.info(f"GetShiftList thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": ShiftTypeModelSchema(many=True).dump(shiftTypeList),
        }, 200

    except Exception as ex:
        app.logger.error(f"GetShiftTypeList thất bại. {ex}")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở server.",
            "ResponseData": None,
        }, 400
    finally:
        app.logger.info("GetShiftTypeList kết thúc.")


# POST api/shift/create
@Shift.route("/create", methods=["POST"])
@admin_required()
def createNewShift():
    try:
        app.logger.info("createNewShift starts. Bắt đầu tạo ca làm việc")
        claims = get_jwt()
        id = claims["id"]
        jsonRequestData = request.get_json()

        # region Khai báo

        Description = (
            jsonRequestData["Description"] if "Description" in jsonRequestData else ""
        )
        # ShiftType = (
        #     jsonRequestData["ShiftType"] if "ShiftType" in jsonRequestData else None
        # )
        StartDate = (
            jsonRequestData["StartDate"] if "StartDate" in jsonRequestData else None
        )
        EndDate = jsonRequestData["EndDate"] if "EndDate" in jsonRequestData else None
        StartTime = (
            jsonRequestData["StartTime"] if "StartTime" in jsonRequestData else None
        )
        FinishTime = (
            jsonRequestData["FinishTime"] if "FinishTime" in jsonRequestData else None
        )
        HasBreak = jsonRequestData["HasBreak"] if "HasBreak" in jsonRequestData else False
        BreakAt = jsonRequestData["BreakAt"] if "BreakAt" in jsonRequestData else None
        BreakEnd = (
            jsonRequestData["BreakEnd"] if "BreakEnd" in jsonRequestData else None
        )
        WorkingHour = jsonRequestData["WorkingHour"] if "WorkingHour" in jsonRequestData else 0
        WorkingDay = jsonRequestData["WorkingDay"] if "WorkingDay" in jsonRequestData else 0

        # endregion

        # region validation

        if not Description or not Description.strip():
            raise ProjectException("Chưa cung cấp tên ca làm việc")
        # if not ShiftType:
        #     raise ProjectException("Chưa cung cấp loại ca làm việc")
        # if not StartDate:
        #     raise ProjectException("Chưa cung cấp ngày bắt đầu")
        if not StartTime:
            raise ProjectException("Chưa cung cấp tên giờ checkin")
        if not FinishTime:
            raise ProjectException("Chưa cung cấp tên giờ checkout")
        if (BreakAt and not BreakEnd) or (not BreakAt and BreakEnd):
            raise ProjectException(
                f"Chưa cung cấp đủ thông tin giờ nghỉ. Bắt đầu {BreakAt}, kết thúc {BreakEnd}."
            )

        # endregion

        newShift = ShiftModel()
        newShift.Description = Description
        # newShift.ShiftType = ShiftType
        newShift.CreatedAt = datetime.now()
        newShift.ModifiedAt = datetime.now()
        newShift.Status = 1
        newShift.CreatedBy = id
        newShift.ModifiedBy = id
        db.session.add(newShift)
        db.session.flush()
        db.session.refresh(newShift)

        shiftDetail = ShiftDetailModel()
        shiftDetail.ShiftId = newShift.Id
        shiftDetail.StartTime = StartTime
        shiftDetail.FinishTime = FinishTime
        shiftDetail.BreakAt = BreakAt
        shiftDetail.BreakEnd = BreakEnd
        shiftDetail.Status = 1
        shiftDetail.HasBreak = HasBreak
        shiftDetail.WorkingDay = WorkingDay
        shiftDetail.WorkingHour = WorkingHour
        shiftDetail.CreatedAt = datetime.now()
        shiftDetail.ModifiedAt = datetime.now()
        shiftDetail.CreatedBy = id
        shiftDetail.ModifiedBy = id
        db.session.add(shiftDetail)
        db.session.commit()
        app.logger.info("createNewShift thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"Id": newShift.Id},
        }, 200
    except ProjectException as ex:
        db.session.rollback()
        app.logger.exception(f"createNewShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Không thể thêm ca làm việc mới. {ex}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"createNewShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("createNewShift finishes. Kết thúc tạo ca làm việc")

# DELETE api/shift
@Shift.route("/", methods=["DELETE"])
@admin_required()
def deleteShift():
    try:
        jsonRequestData = request.get_json()
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        claims = get_jwt()
        id = claims["id"]

        # region validate

        if "IdList" not in jsonRequestData:
            raise ProjectException("Không tìm thấy mã ca làm việc trong request.")
        IdList = jsonRequestData["IdList"]
        if not IdList or len(IdList) == 0:
            raise ProjectException("Không tìm thấy mã ca làm việc trong request.")

        # endregion

        shiftList = db.session.execute(
            db.select(ShiftModel).where(ShiftModel.Id.in_(jsonRequestData["IdList"]))
        ).scalars().all()
        ShiftModel.DeleteBulkByIds([shift.Id for shift in shiftList])
        app.logger.info("deleteShift thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200
    except ProjectException as pEx:
        app.logger.exception(f"deleteShift thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"deleteShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200

# PUT api/shift
@Shift.route("/update", methods=["PUT"])
@admin_required()
def updateShift():
    try:
        app.logger.info("updateShift bắt đầu.")
        claims = get_jwt()
        id = claims["id"]
        jsonRequestData = request.get_json()

        shiftId = int(jsonRequestData["Id"]) if "Id" in jsonRequestData else None
        Description = (
            jsonRequestData["Description"] if "Description" in jsonRequestData else None
        )
        StartTime = (
            jsonRequestData["StartTime"] if "StartTime" in jsonRequestData else None
        )
        FinishTime = (
            jsonRequestData["FinishTime"] if "FinishTime" in jsonRequestData else None
        )
        HasBreak = jsonRequestData["HasBreak"] if "HasBreak" in jsonRequestData else None
        BreakAt = jsonRequestData["BreakAt"] if "BreakAt" in jsonRequestData else None
        BreakEnd = (
            jsonRequestData["BreakEnd"] if "BreakEnd" in jsonRequestData else None
        )
        WorkingDay = jsonRequestData["WorkingDay"] if "WorkingDay" in jsonRequestData else None
        WorkingHour = jsonRequestData["WorkingHour"] if "WorkingHour" in jsonRequestData else None

        # region validate

        if not shiftId:
            raise ProjectException("Không tìm thấy mã ca làm việc trong request.")

        # endregion

        #region validate

        shift = ShiftModel.query.filter_by(Id = shiftId).first()

        if not shift:
            raise ProjectException(f"Không tồn tại ca làm việc Id [{shiftId}]")
        shiftDetail = db.session.execute(
            select(ShiftDetailModel).where(
                and_(ShiftDetailModel.ShiftId == shiftId, ShiftDetailModel.Status == 1)
            )
        ).scalar()
        if not shiftDetail:
            raise ProjectException(
                f"Không tồn tại thông tin chi tiết ca làm việc Id [{shiftId}]"
            )
        
        #endregion

        if Description and shift.Description != Description:
            shift.Description = Description
        if StartTime and shiftDetail.StartTime != StartTime:
            shiftDetail.StartTime = StartTime
        if FinishTime and shiftDetail.FinishTime != FinishTime:
            shiftDetail.FinishTime = FinishTime
        if HasBreak:
            if shiftDetail.BreakAt != BreakAt:
                shiftDetail.BreakAt = BreakAt
            if shiftDetail.BreakEnd != BreakEnd:
                shiftDetail.BreakEnd = BreakEnd
        else:
            shiftDetail.BreakEnd = None
            shiftDetail.BreakAt = None
        shiftDetail.HasBreak = HasBreak
        shiftDetail.WorkingHour = WorkingHour
        shiftDetail.WorkingDay = WorkingDay
        shiftDetail.ModifiedAt = datetime.now()
        shiftDetail.ModifiedBy = id
        shift.ModifiedBy = id
        shift.ModifiedAt = datetime.now()
        db.session.commit()
        app.logger.info(f"updateShift Id[{shiftId}] thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "Shift": shiftSchema.dump(shift),
                "Detail": ShiftDetailSchema().dump(shiftDetail),
            },
        }, 200

    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"UpdateShift thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200

    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"UpdateShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("updateShift kết thúc.")

# POST api/shif/detail
@Shift.route("/detail", methods=["GET"])
@admin_required()
def GetShiftDetail():
    try:
        app.logger.info(f"GetShiftDetail bắt đầu")
        claims = get_jwt()
        id = claims["id"]
        args = request.args
        Id = int(args["Id"]) if "Id" in args else None
        if not Id:
            raise ProjectException(f"Không tìm thấy mã ca làm việc {Id} trong yêu cầu.")

        existShift = ShiftModel.query.filter_by(Id=Id).first()
        if not existShift:
            raise ProjectException(f"Ca làm việc {Id} không được tìm thấy trong hệ thống.")
        shiftDetail = db.session.execute(select(ShiftDetailModel)
                                        .where(and_(ShiftDetailModel.ShiftId == Id, ShiftDetailModel.Status ==1))
                                        ).scalar()
        app.logger.info(f"GetShiftDetail mã ca làm việc [{Id}] thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "Shift": shiftSchema.dump(existShift),
                "Detail": ShiftDetailSchema().dump(shiftDetail)
            },
        }, 200
    except ProjectException as pEx:
        app.logger.exception(f"GetShiftDetail thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"GetShiftDetail thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"GetShiftDetail kết thúc")

#endregion

#region Phân ca làm việc

# POST api/shift/assignment
@Shift.route("/assignment", methods=["POST"])
@admin_required()
def AssignShift():
    try:
        app.logger.info("AssignShift bắt đầu")
        jsonRequestData = request.get_json()
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        claims = get_jwt()
        id = claims["id"]

        # region Khai báo

        description = jsonRequestData["Description"] if "Description" in jsonRequestData else None
        shiftId = jsonRequestData["ShiftId"] if "ShiftId" in jsonRequestData else None
        departmentList = jsonRequestData["DepartmentList"] if "DepartmentList" in jsonRequestData else []
        employeeList = jsonRequestData["EmployeeList"] if "EmployeeList" in jsonRequestData else []
        note = jsonRequestData["Note"] if "Note" in jsonRequestData else ""
        startDate = jsonRequestData["StartDate"] if "StartDate" in jsonRequestData else None
        endDate = jsonRequestData["EndDate"] if "EndDate" in jsonRequestData else None
        daysInWeek = jsonRequestData["DaysInWeek"] if "DaysInWeek" in jsonRequestData else None
        targetType = jsonRequestData["TargetType"] if "TargetType" in jsonRequestData else None

        # endregion
        # region validate

        if not description:
            raise ProjectException(
                "Không tìm thấy tên bảng phân ca trong truy vấn."
            )
        if not shiftId:
            raise ProjectException(f"Không tìm thấy mã ca làm việc trong truy vấn")
        shiftDetail = ShiftDetailModel.query.filter_by(ShiftId=shiftId).first()
        if not shiftDetail:
            raise ProjectException(f"Không tìm thấy ca làm việc có mã {shiftId}")
        if not startDate:
            raise ProjectException(f"Không tìm thấy ngày bắt đầu trong truy vấn.")
        if not endDate:
            raise ProjectException(f"Không tìm thấy ngày kết thúc trong truy vấn.")
        if not daysInWeek or not len(daysInWeek):
            raise ProjectException(f"Không tìm thấy ngày trong tuần được áp dụng bảng phân ca trong truy vấn.")
        if not targetType:
            raise ProjectException(f"Không tìm thấy kiểu phân ca cho bảng phân ca trong truy vấn.")

        if targetType == TargetType.Employee.value:
            if not len(employeeList):
                raise ProjectException(f"Không tìm thấy các nhân viên được áp dụng bảng phân ca trong truy vấn.")
        elif targetType == TargetType.Department.value:
            if not len(departmentList):
                raise ProjectException(f"Không tìm thấy các  phòng ban được áp dụng bảng phân ca trong truy vấn.")
        else:
            raise ProjectException(f"Không hỗ trợ phân ca kiểu {targetType}")

        # endregion


        # region Kiểm tra có bị lồng phân ca không.

        # CheckIfExist(
        #     assignType=assignType, shiftDetail=shiftDetail, targetList=targetArray
        # )

        # endregion

        # region Thêm phân ca mới

        newShiftAssignment = ShiftAssignment()
        newShiftAssignment.Description = description
        newShiftAssignment.TargetType = targetType
        newShiftAssignment.ShiftId = shiftId
        newShiftAssignment.DaysInWeek = daysInWeek
        newShiftAssignment.ShiftDetailId = shiftDetail.Id
        newShiftAssignment.StartDate = startDate
        newShiftAssignment.EndDate = endDate
        newShiftAssignment.Note = note
        newShiftAssignment.CreatedBy = id
        newShiftAssignment.ModifiedBy = id
        db.session.add(newShiftAssignment)
        db.session.flush()
        db.session.refresh(newShiftAssignment)

        # endregion

        # region Thêm chi tiết phân ca mới


        if targetType == TargetType.Employee.value:
            values = list()
            for employeeId in employeeList:
                values.append(     
                    {
                        "ShiftAssignmentId": newShiftAssignment.Id,
                        "EmployeeId": employeeId,
                        "CreatedAt": datetime.now(),
                        "ModifiedAt": datetime.now(),
                        "CreatedBy": id,
                        "ModifiedBy": id,
                    }
                )
            db.session.execute(insert(ShiftAssignmentEmployee), values)
        elif targetType == TargetType.Department.value:
            values = list()
            for departmentId in departmentList:
                    values.append(     
                    {
                        "ShiftAssignmentId": newShiftAssignment.Id,
                        "DepartmentId": departmentId,
                        "CreatedAt": datetime.now(),
                        "ModifiedAt": datetime.now(),
                        "CreatedBy": id,
                        "ModifiedBy": id,
                    }
                )
                # values.append(ShiftAssignmentDepartment (shift_assignment_id=newShiftAssignment.Id, department_id=department_id))
            db.session.execute(insert(ShiftAssignmentDepartment), values)

        # values = []
        # for target in targetArray:
        #     values.append(
        #         {
        #             "ShiftAssignmentId": newShiftAssignment.Id,
        #             "Target": target,
        #             "CreatedAt": datetime.now(),
        #             "ModifiedAt": datetime.now(),
        #             "CreatedBy": id,
        #             "ModifiedBy": id,
        #         }
        #     )
        

        # if len(values) == 0:
        #     db.session.rollback()
        #     app.logger.info("AssignShift thành công")
        #     return {
        #         "Status": 0,
        #         "Description": f"Không thể tạo phân ca do chưa có đối tượng được phân ca.",
        #         "ResponseData": None,
        #     }, 200
        # db.session.execute(insert(ShiftAssignmentDetail), values)

        # endregion

        db.session.commit()
        app.logger.info("AssignShift thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"Id": newShiftAssignment.Id},
        }, 200
    except ProjectException as pEx:
        app.logger.exception(f"AssignShift thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"AssignShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Không thể phân ca làm việc.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("AssignShift kết thúc")


def CheckIfExist(assignType: int, targetList: list, shiftDetail: ShiftDetailModel):
    targetArray = targetList
    for target in targetArray:
        existAssignmentList = db.session.execute(
            select(
                ShiftAssignmentDetail.Target,
                ShiftDetailModel.StartDate,
                ShiftDetailModel.EndDate,
            )
            .select_from(ShiftAssignmentDetail)
            .join(
                ShiftAssignment,
                and_(
                    ShiftAssignment.AssignType == assignType,
                    ShiftAssignmentDetail.ShiftAssignmentId == ShiftAssignment.Id,
                ),
            )
            .join(
                ShiftDetailModel,
                and_(ShiftAssignment.ShiftDetailId == ShiftDetailModel.Id),
            )
            .where(
                and_(
                    ShiftAssignment.AssignType == assignType,
                    ShiftAssignmentDetail.Status == "1",
                    ShiftAssignmentDetail.Target == target,
                )
            )
        ).all()
        for existAssignment in existAssignmentList:
            if not (
                existAssignment.StartDate > shiftDetail.EndDate
                or shiftDetail.StartDate > existAssignment.EndDate
            ):
                content = ""
                if assignType == 1:
                    department = DepartmentModel.query.filter_by(Id=target).first()
                    content = f"phòng ban {department.Name} ({target})"
                elif assignType == 2:
                    employee = EmployeeModel.query.filter_by(Id=target).first()
                    content = (
                        f"nhân viên {employee.LastName} {employee.FirstName} ({target})"
                    )
                raise ProjectException(f"Phân ca {content} bị lồng.")


# GET api/shift/assignment/list
@Shift.route("/assignment/list", methods=["GET"])
@admin_required()
def getShiftAssignmentList():
    try:
        app.logger.info("getShiftAssignmentList bắt đầu")

        #region khai bao

        args = request.args
        page = None
        pageSize = None
        if "Page" in args:
            page = int(args["Page"])
        if "PageSize" in args:
            pageSize = int(args["PageSize"])

        #endregion

        data = []
        result = ShiftAssignment.QueryMany(Page=page, PerPage=pageSize)
        shiftAssignmentList = result["Items"]
        total = result["Total"]

        for assignment in shiftAssignmentList:
            temp = ShiftAssignmentSchema().dump(assignment)
            temp["EmployeeList"] = []
            temp["DepartmentList"] = []
            if assignment["TargetType"] == TargetType.Employee.value:
                    # query = db.select(vShiftAssignmentDetail.EmployeeName) \
                    #         .where(and_(vShiftAssignmentDetail.Id == assignment["Id"], vShiftAssignmentDetail.TargetType ==  TargetType.Employee.value))
                query = db.select(EmployeeModel).join(ShiftAssignmentEmployee, ShiftAssignmentEmployee.EmployeeId == EmployeeModel.Id).where(and_(ShiftAssignmentEmployee.ShiftAssignmentId == assignment["Id"]))
                EmployeeList = db.session.execute(query).scalars().all()
                temp["EmployeeList"] = EmployeeSchema(many=True).dump(EmployeeList)
            elif assignment["TargetType"] == TargetType.Department.value:
                    # query = db.select(vShiftAssignmentDetail.DepartmentName)\
                    # .where(and_(vShiftAssignmentDetail.Id == assignment["Id"], vShiftAssignmentDetail.TargetType == TargetType.Department.value))
                query = db.select(DepartmentModel).join(ShiftAssignmentDepartment, ShiftAssignmentDepartment.DepartmentId == DepartmentModel.Id).where(and_(ShiftAssignmentDepartment.ShiftAssignmentId == assignment["Id"]))
                DepartmentList = db.session.execute(query).scalars().all()

                temp["DepartmentList"] = DepartmentSchema(many=True).dump(DepartmentList)
            else: pass
            data.append(temp)


        app.logger.exception(f"getShiftAssignmentList thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "ShiftAssignmentList": data,
                "Total": total
            }
        }, 200
    except ProjectException as pEx:
        app.logger.exception(
            f"getShiftAssignmentList thất bại. Có exception[{str(pEx)}]"
        )
        return {
            "Status": 0,
            "Description": f"Không thể truy cập được thông tin phân ca. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(
            f"getShiftAssignmentList thất bại. Có exception[{str(ex)}]"
        )
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Không thể truy cập được thông tin phân ca",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("getShiftAssignmentList kết thúc")


# POST api/shift/assignment/detail
@Shift.route("/assignment/detail", methods=["POST"])
@admin_required()
def getShiftAssignmentDetail():
    try:
        app.logger.info("getShiftAssignmentDetail bắt đầu")
        jsonRequestData = request.get_json()

        # region validate

        if "Id" not in jsonRequestData:
            raise ProjectException("Không tìm thấy thông tin mã phân ca")

        # endregion

        id = jsonRequestData["Id"]
        assignment = ShiftAssignment.query.filter_by(Id=id).first()
        if not assignment:
            raise PorjectException(f"Không tìm thấy bảng phân ca có mã f{Id}")
        assignmentDetail = assignment.QueryDetails()
        if not assignmentDetail:
            raise PorjectException(f"Không tìm thấy thông tin chi tiết của bảng phân ca có mã f{Id}")
        
        shiftDetail = vShiftDetail.query.filter_by(Id=assignment.ShiftId).first()

        app.logger.info("getShiftAssignmentDetails thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "Assignment": ShiftAssignmentSchema().dump(assignment),
                "ShiftDetail": vShiftDetailSchema().dump(shiftDetail),
                "DepartmentList":assignmentDetail["DepartmentList"],
                "EmployeeList": assignmentDetail["EmployeeList"]
            },
        }, 200
    except ProjectException as pEx:
        app.logger.exception(
            f"getShiftAssignmentDetails thất bại. Có exception[{str(pEx)}]"
        )
        return {
            "Status": 0,
            "Description": f"Không thể truy cập được thông tin phân ca. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"UpdateShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Không thể truy cập được thông tin phân ca",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("getShiftAssignmentDetail kết thúc")


# POST api/shift/assignment/all-type
@Shift.route("/assignment/all-type", methods=["GET", "POST"])
@jwt_required()
def GetAssignmentType():
    try:
        shiftAssignmentTypeList = db.session.execute(
            select(
                ShiftAssignmentType.Id,
                ShiftAssignmentType.Name,
                ShiftAssignmentType.Name2,
                ShiftAssignmentType.CreatedAt,
                ShiftAssignmentType.CreatedBy,
            ).where(ShiftAssignmentType.Status == Status.Active)
        ).all()
        response = [r._asdict() for r in shiftAssignmentTypeList]
        app.logger.info("GetAssignmentTypes thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": response,
        }, 200
    except ProjectException as pEx:
        app.logger.exception(f"GetAssignmentTypes thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Không thể truy cập được thông tin kiểu phân ca. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"GetAssignmentTypes thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Không thể truy cập được thông tin kiểu phân ca.",
            "ResponseData": None,
        }, 200


# POST api/shift/assignment/update
@Shift.route("/assignment/update", methods=["POST"])
@admin_required()
def UpdateAssignment():
    try:
        app.logger.info(f"UpdateAssignment bắt đầu")
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        claims = get_jwt()
        id = claims["id"]
        jsonRequestData = request.get_json()

        # region validate

        if "Id" not in jsonRequestData:
            raise ProjectException("Không tìm thấy thông tin mã phân ca")

        assignmentId = jsonRequestData["Id"]
        description = (
            None
            if "Description" not in jsonRequestData
            else jsonRequestData["Description"]
        )
        note = None if "Note" not in jsonRequestData else jsonRequestData["Note"]
        DepartmentList = (
            None
            if "DepartmentList" not in jsonRequestData
            else jsonRequestData["DepartmentList"]
        )
        EmployeeList = (
            None
            if "EmployeeList" not in jsonRequestData
            else jsonRequestData["EmployeeList"]
        )
        shiftId = (
            None
            if "ShiftId" not in jsonRequestData
            else jsonRequestData["ShiftId"]
        )
        startDate = jsonRequestData["StartDate"] if "StartDate" in jsonRequestData else None
        endDate = jsonRequestData["EndDate"] if "EndDate" in jsonRequestData else None
        daysInWeek = jsonRequestData["DaysInWeek"] if "DaysInWeek" in jsonRequestData else None
        assignmentType = jsonRequestData["TargetType"] if "TargetType" in jsonRequestData else None

        # endregion

        shiftAssignment = ShiftAssignment.query.filter_by(Id=assignmentId).first()
        if not shiftAssignment:
            raise ProjectException("Không tìm thấy bảng phân ca.")
            
        # detailTargetList = db.session.execute(
        #     select(ShiftAssignmentDetail.Target).where(
        #         and_(
        #             ShiftAssignmentDetail.ShiftAssignmentId == assignmentId,
        #             ShiftAssignmentDetail.Status == "1",
        #         )
        #     )
        # ).scalars().all()

        detailTargetList = shiftAssignment.QueryDetails()

        if description and description != shiftAssignment.Description:
            shiftAssignment.Description = description
        if note and note != shiftAssignment.Note:
            shiftAssignment.Note = note
        if shiftId and shiftId != shiftAssignment.ShiftId:
            shiftAssignment.ShiftId = shiftId
            shiftDetail = ShiftDetailModel.query.filter_by(ShiftId=shiftId).first()
            shiftAssignment.shiftDetailId = shiftDetail.Id
        if endDate and endDate != shiftAssignment.EndDate:
            shiftAssignment.EndDate = endDate
        if startDate and startDate != shiftAssignment.StartDate:
            shiftAssignment.StartDate = startDate
        if daysInWeek and daysInWeek != shiftAssignment.DaysInWeek:
            shiftAssignment.DaysInWeek = daysInWeek

        insertIdArray = []
        removeArray = []

        if assignmentType == shiftAssignment.TargetType:
            if assignmentType == TargetType.Employee.value:
                removeArray = list(filter(lambda x: x not in EmployeeList , detailTargetList["EmployeeList"] ))
                insertIdArray = list(filter(lambda x: x not in detailTargetList, EmployeeList))
            elif assignmentType == TargetType.Department.value:
                removeArray = list(filter(lambda x: x not in DepartmentList, detailTargetList["DepartmentList"]))
                insertIdArray = list(filter(lambda x: x not in detailTargetList, DepartmentList))     
            if len(removeArray):
                # ShiftAssignmentDetail.DisableBulk(removeArray)
                shiftAssignment.RemoveBulkByTargets(removeArray)
            if len(insertIdArray):
                shiftAssignment.InsertManyTargets(IdList=insertIdArray, userId=id)

        else:
            if assignmentType == TargetType.Department.value:
                insertIdArray.extend(DepartmentList)
            if assignmentType == TargetType.Employee.value:
                insertIdArray.extend(EmployeeList)
            # insertIdArray.extend(EmployeeList if assignmentType == 1 else EmployeeList if assignmentType == 2 else [])

            if len(removeArray):
                # ShiftAssignmentDetail.DisableBulk(removeArray)
                shiftAssignment.RemoveBulkByTargets(TargetList=removeArray)
            shiftAssignment.TargetType = assignmentType
            if len(insertIdArray):
                shiftAssignment.InsertManyTargets(IdList=insertIdArray, userId=id)


        # if assignmentType and assignmentType != shiftAssignment.TargetType:
        #     shiftAssignment.TargetType = assignmentType
        #     removeArray.extend(detailTargetList)
        #     insertIdArray.extend(EmployeeList if assignmentType == 1 else DepartmentList if assignmentType == 2 else [])
        # else:
        #     if assignmentType == TargetType.Employee.value:
        #         removeArray = list(filter(lambda x: x not in EmployeeList , detailTargetList ))
        #         insertIdArray = list(filter(lambda x: x not in detailTargetList, EmployeeList))
                
        #     elif assignmentType == TargetType.Department.value:
        #         removeArray = list(filter(lambda x: x not in DepartmentList, detailTargetList))
        #         insertIdArray = list(filter(lambda x: x not in detailTargetList, DepartmentList))     

        # if len(removeArray):
        #     # ShiftAssignmentDetail.DisableBulk(removeArray)
        #     shiftAssignment.RemoveBulkByTargets(removeArray)
        # if len(insertIdArray):
        #     shiftAssignment.InsertManyTargets(IdList=insertIdArray, userId=id)

        db.session.commit()
        app.logger.info(f"UpdateAssignment [{assignmentId}] thành công")
        return {
            "Status": 1,
            "Description": "Đã cập nhật",
            "ResponseData": None,
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"UpdateAssignment thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"UpdateAssignment thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"UpdateAssignment kết thúc")


# DELETE api/shift/assignment
@Shift.route("/assignment", methods=["DELETE"])
@admin_required()
def DeleteShiftAssignment():
    try:
        assignmentId = int(request.args["Id"])
        exist = ShiftAssignment.query.filter_by(Id=assignmentId).first()
        if not exist:
            raise ProjectException(f"Không tìm thấy bảng phân ca có mã {assignmentId}")
        detail = []
        if exist.TargetType == TargetType.Department.value:
            query = db.delete(ShiftAssignmentDepartment).where(ShiftAssignmentDepartment.ShiftAssignmentId==assignmentId)
        elif exist.TargetType == TargetType.Employee.value:
            query = db.delete(ShiftAssignmentEmployee).where(ShiftAssignmentEmployee.ShiftAssignmentId==assignmentId)
        if detail: 
            db.session.execute(query)
        db.session.execute(db.delete(ShiftAssignment).where(ShiftAssignment.Id==assignmentId))
        db.session.commit()
        return {
            "Status": 1,
            "Description": "Đã xóa",
            "ResponseData": {
                "AssignmentId": ShiftAssignmentSchema().dump(exist),
            },
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"DeleteShiftAssignment thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"DeleteShiftAssignment thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"DeleteShiftAssignment kết thúc")


#endregion