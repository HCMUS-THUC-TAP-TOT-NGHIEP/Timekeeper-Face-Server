import time
from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request
from flask_json import json_response
from sqlalchemy import and_, case, delete, func, insert, or_, select

from src.authentication.model import UserModel
from src.db import db
from src.department.model import DepartmentModel
from src.designation.model import Designation
from src.employee.model import EmployeeModel
from src.extension import ProjectException, object_as_dict
from src.jwt import get_jwt, get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.shift.model import (
    ShiftAssignment,
    ShiftAssignmentDetail,
    ShiftAssignmentSchema,
    ShiftAssignmentType,
    ShiftDetailModel,
    ShiftModel,
    ShiftTypeModel,
    ShiftTypeModelSchema,
    Status,
    TargetType,
    shiftListResponseSchema,
    shiftListSchema,
    ShiftDetailSchema,
)

Shift = Blueprint("shift", __name__)


# GET api/shift/list
@Shift.route("/list", methods=["GET"])
@admin_required()
def GetShiftList():
    try:
        args = request.args.to_dict()
        page = 1
        perPage = 10
        if "Page" in args:
            page = int(args["Page"])
        if "PerPage" in args:
            perPage = int(args["PerPage"])

        shiftList = db.session.execute(
            select(
                ShiftModel.Id,
                ShiftModel.Description,
                ShiftDetailModel.StartTime,
                ShiftDetailModel.FinishTime,
                ShiftDetailModel.StartDate,
                ShiftDetailModel.EndDate,
                ShiftDetailModel.BreakAt,
                ShiftDetailModel.BreakEnd,
                ShiftModel.CreatedAt,
                ShiftModel.ShiftType,
                ShiftTypeModel.Description.label("ShiftTypeText"),
                ShiftModel.Status,
                ShiftDetailModel.Note,
                ShiftDetailModel.DayIndexList,
                ShiftDetailModel.BreakMinutes,
            )
            .select_from(ShiftModel)
            .join(
                ShiftDetailModel,
                and_(
                    ShiftDetailModel.ShiftId == ShiftModel.Id,
                    ShiftDetailModel.Status == 1,
                ),
                isouter=True,
            )
            .join(
                ShiftTypeModel,
                ShiftTypeModel.Id == ShiftModel.ShiftType,
                isouter=True,
            )
            .order_by(ShiftModel.Id)
        ).all()
        app.logger.info(f"GetShiftList thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": shiftListSchema.dump(shiftList),
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
            "Description": f"Có lỗi ở server. Không tìm thấy ca làm việc nào",
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
        jsonRequestData = request.get_json()
        claims = get_jwt()
        id = claims["id"]

        # region Khai báo

        Description = (
            jsonRequestData["Description"] if "Description" in jsonRequestData else None
        )
        ShiftType = (
            jsonRequestData["ShiftType"] if "ShiftType" in jsonRequestData else None
        )
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
        BreakAt = jsonRequestData["BreakAt"] if "BreakAt" in jsonRequestData else None
        BreakEnd = (
            jsonRequestData["BreakEnd"] if "BreakEnd" in jsonRequestData else None
        )
        DayIndexList = (
            jsonRequestData["DayIndexList"]
            if "DayIndexList" in jsonRequestData
            else None
        )
        Note = jsonRequestData["Note"] if "Note" in jsonRequestData else None

        # endregion

        # region validation

        if not Description or not Description.strip():
            raise ProjectException("Chưa cung cấp tên ca làm việc")
        if not ShiftType:
            raise ProjectException("Chưa cung cấp loại ca làm việc")
        if not StartDate:
            raise ProjectException("Chưa cung cấp ngày bắt đầu")
        if not StartTime:
            raise ProjectException("Chưa cung cấp tên giờ checkin")
        if not FinishTime:
            raise ProjectException("Chưa cung cấp tên giờ checkout")
        if (BreakAt and not BreakEnd) or (not BreakAt and BreakEnd):
            raise ProjectException(
                f"Chưa cung cấp đủ thông tin giờ nghỉ. Bắt đầu {BreakAt}, kết thúc {BreakEnd}."
            )
        if not DayIndexList or len(DayIndexList) == 0:
            raise ProjectException(
                f"Chưa cung cấp đủ thông tin những ngày áp dụng trong tuần."
            )

        # endregion

        newShift = ShiftModel()
        newShift.Description = Description
        newShift.ShiftType = ShiftType
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
        shiftDetail.StartDate = StartDate
        shiftDetail.EndDate = EndDate
        shiftDetail.StartTime = StartTime
        shiftDetail.FinishTime = FinishTime
        shiftDetail.BreakAt = BreakAt
        shiftDetail.BreakEnd = BreakEnd
        if BreakAt and BreakEnd:
            BreakMinutes = datetime.strptime(BreakEnd, "%H:%M:%S") - datetime.strptime(
                BreakAt, "%H:%M:%S"
            )
            shiftDetail.BreakMinutes = divmod(BreakMinutes.total_seconds(), 60)[0]
        shiftDetail.Note = Note
        shiftDetail.DayIndexList = DayIndexList
        shiftDetail.CreatedAt = datetime.now()
        shiftDetail.ModifiedAt = datetime.now()
        shiftDetail.CreatedBy = id
        shiftDetail.ModifiedBy = id
        shiftDetail.Status = 1
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
            "Description": f"Có lỗi ở máy chủ. Không thể thêm ca làm việc mới",
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

        # region validate

        if "IdList" not in jsonRequestData:
            raise ProjectException("Không tìm thấy mã ca làm việc trong request.")
        IdList = jsonRequestData["IdList"]
        if not IdList or len(IdList) == 0:
            raise ProjectException("Không tìm thấy mã ca làm việc trong request.")

        # endregion

        result = db.session.execute(
            delete(ShiftModel).where(ShiftModel.Id.in_(jsonRequestData["IdList"]))
        )
        db.session.commit()
        app.logger.info("deleteShift thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"deleteShift thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Không thể xóa ca làm việc. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"deleteShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Không thể xóa ca làm việc",
            "ResponseData": None,
        }, 200


# PUT api/shift
@Shift.route("/update", methods=["PUT"])
@admin_required()
def updateShift():
    try:
        app.logger.info("updateShift bắt đầu.")
        jsonRequestData = request.get_json()
        claims = get_jwt()
        id = claims["id"]

        shiftId = jsonRequestData["Id"] if "Id" in jsonRequestData else None
        Description = (
            jsonRequestData["Description"] if "Description" in jsonRequestData else None
        )
        ShiftType = (
            jsonRequestData["ShiftType"] if "ShiftType" in jsonRequestData else None
        )
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
        BreakAt = jsonRequestData["BreakAt"] if "BreakAt" in jsonRequestData else None
        BreakEnd = (
            jsonRequestData["BreakEnd"] if "BreakEnd" in jsonRequestData else None
        )
        DayIndexList = (
            jsonRequestData["DayIndexList"]
            if "DayIndexList" in jsonRequestData
            else None
        )
        Note = jsonRequestData["Note"] if "Note" in jsonRequestData else None

        # region validate

        if not shiftId:
            raise ProjectException("Không tìm thấy mã ca làm việc trong request.")

        # endregion

        shift = db.session.execute(
            select(ShiftModel).filter_by(Id=shiftId)
        ).scalar_one_or_none()
        shiftDetail = db.session.execute(
            select(ShiftDetailModel).where(
                and_(ShiftDetailModel.ShiftId == shiftId, ShiftDetailModel.Status == 1)
            )
        ).scalar_one_or_none()

        if not shift:
            raise ProjectException(f"Không tồn tại ca làm việc Id [{shiftId}]")
        if not shiftDetail:
            raise ProjectException(
                f"Không tồn tại thông tin chi tiết ca làm việc Id [{shiftId}]"
            )
        hasSomeChanges = False

        if shift.Description != Description:
            shift.Description = Description
            hasSomeChanges = True
        if shift.ShiftType != ShiftType:
            shift.ShiftType = ShiftType
            hasSomeChanges = True
        if hasSomeChanges:
            shift.ModifiedBy = id
            shift.ModifiedAt = datetime.now()
        newShiftDetail = ShiftDetailModel()
        if shiftDetail.StartDate != StartDate:
            newShiftDetail.StartDate = StartDate
            hasSomeChanges = True
        if shiftDetail.EndDate != EndDate:
            newShiftDetail.EndDate = EndDate
            hasSomeChanges = True
        if shiftDetail.StartTime != StartTime:
            newShiftDetail.StartTime = StartTime
            hasSomeChanges = True
        if shiftDetail.FinishTime != FinishTime:
            newShiftDetail.FinishTime = FinishTime
            hasSomeChanges = True
        if shiftDetail.BreakAt != BreakAt:
            newShiftDetail.BreakAt = BreakAt
            hasSomeChanges = True
        if shiftDetail.BreakEnd != BreakEnd:
            newShiftDetail.BreakEnd = BreakEnd
            hasSomeChanges = True
        if BreakAt and BreakEnd:
            newShiftDetail.BreakMinutes = divmod(
                (
                    datetime.strptime(BreakEnd, "%H:%M:%S")
                    - datetime.strptime(BreakAt, "%H:%M:%S")
                ).total_seconds(),
                60,
            )[0]
        else:
            newShiftDetail.BreakMinutes = 0
        if shiftDetail.DayIndexList != DayIndexList:
            newShiftDetail.DayIndexList = DayIndexList
        if shiftDetail.Note != Note:
            newShiftDetail.Note = Note
        if hasSomeChanges:
            newShiftDetail.Status = 1
            newShiftDetail.ShiftId = shift.Id
            newShiftDetail.CreatedAt = datetime.now()
            newShiftDetail.CreatedBy = id
            newShiftDetail.ModifiedAt = datetime.now()
            newShiftDetail.ModifiedBy = id
            shiftDetail.Status = 0
            shiftDetail.ModifiedAt = datetime.now()
            shiftDetail.ModifiedBy = id
            db.session.add(newShiftDetail)
        else:
            raise ProjectException(
                f"Không thông tin thay đổi trong ca làm việc Id[{shiftId}]"
            )
        db.session.commit()
        app.logger.info(f"updateShift Id[{shiftId}] thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200

    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"UpdateShift thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Không thể cập nhật ca làm việc. {pEx}",
            "ResponseData": None,
        }, 200

    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"UpdateShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Không thể cập nhật ca làm việc",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("updateShift kết thúc.")


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

        # region validate

        user = UserModel.query.filter_by(EmailAddress=email).first()
        if user is None:
            raise ProjectException("Máy chủ không tìm thấy người dùng " + email)

        if "Description" not in jsonRequestData:
            raise ProjectException(
                "Máy chủ không tìm thấy tiêu đề hay mô tả của ca làm việc."
            )
        if "AssignType" not in jsonRequestData:
            raise ProjectException("Máy chủ không tìm kiểu phân ca.")
        if "ShiftId" not in jsonRequestData:
            raise ProjectException("Máy chủ không tìm thấy loại ca.")

        # endregion

        # region Khai báo

        description = jsonRequestData["Description"]
        assignType = jsonRequestData["AssignType"]
        shiftId = jsonRequestData["ShiftId"]
        departmentList = (
            []
            if "DepartmentId" not in jsonRequestData
            else jsonRequestData["DepartmentId"]
        )
        employeeList = (
            [] if "EmployeeId" not in jsonRequestData else jsonRequestData["EmployeeId"]
        )
        note = "" if "Note" not in jsonRequestData else jsonRequestData["Note"]

        # endregion

        # region Kiểm tra có bị lồng phân ca không.

        shiftDetail = db.session.execute(
            select(ShiftDetailModel).where(
                and_(
                    ShiftDetailModel.ShiftId == shiftId,
                    ShiftDetailModel.Status == 1,
                )
            )
        ).scalar_one_or_none()
        if not shiftDetail:
            raise ProjectException(
                f"Không tìm thấy thông tin của ca làm việc {shiftId}"
            )

        if assignType != 1 and assignType != 2:
            raise ProjectException(f'Chưa hỗ trợ loại phân ca có mã "{assignType}"')
        targetArray = []
        if assignType == 1:
            targetArray = departmentList
        elif assignType == 2:
            targetArray = employeeList
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
                
                pass
        # endregion

        # region Thêm phân ca mới

        newShiftAssignment = ShiftAssignment()
        newShiftAssignment.Description = description
        newShiftAssignment.AssignType = assignType
        newShiftAssignment.ShiftId = shiftId
        newShiftAssignment.ShiftDetailId = shiftDetail.Id
        newShiftAssignment.StartDate = shiftDetail.StartDate
        newShiftAssignment.EndDate = shiftDetail.EndDate
        newShiftAssignment.Note = note
        newShiftAssignment.CreatedBy = id
        newShiftAssignment.ModifiedBy = id
        newShiftAssignment.CreatedAt = datetime.now()
        newShiftAssignment.ModifiedAt = datetime.now()
        db.session.add(newShiftAssignment)
        db.session.flush()
        db.session.refresh(newShiftAssignment)

        # endregion

        # region Thêm chi tiết phân ca mới

        values = []
        for department in departmentList:
            values.append(
                {
                    "ShiftAssignmentId": newShiftAssignment.Id,
                    "Target": department,
                    "TargetType": TargetType.Department.value,
                    "CreatedAt": datetime.now(),
                    "ModifiedAt": datetime.now(),
                    "CreatedBy": id,
                    "ModifiedBy": id,
                }
            )
        for employee in employeeList:
            values.append(
                {
                    "ShiftAssignmentId": newShiftAssignment.Id,
                    "Target": employee,
                    "TargetType": TargetType.Employee.value,
                    "CreatedAt": datetime.now(),
                    "ModifiedAt": datetime.now(),
                    "CreatedBy": id,
                    "ModifiedBy": id,
                }
            )
        if len(values) == 0:
            db.session.rollback()
            app.logger.info("AssignShift thành công")
            return {
                "Status": 1,
                "Description": f"Không thể tạo phân ca do chưa có đối tượng được phân ca.",
                "ResponseData": None,
            }, 200
        db.session.execute(insert(ShiftAssignmentDetail), values)

        # endregion

        # db.session.commit()
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
            "Description": f"Không thể phân ca làm việc.",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"AssignShift thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Không thể phân ca làm việc.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("AssignShift kết thúc")


# GET api/shift/assignment/list
@Shift.route("/assignment/list", methods=["GET"])
@admin_required()
def getShiftAssignmentList():
    try:
        app.logger.info("getShiftAssignmentList bắt đầu")
        shiftAssignmentList = db.session.execute(
            select(
                ShiftAssignment.Id,
                ShiftAssignment.ShiftId,
                ShiftAssignment.Description,
                ShiftAssignment.StartDate,
                ShiftAssignment.EndDate,
                ShiftAssignment.AssignType,
                ShiftAssignment.Note,
                ShiftAssignment.Status,
                ShiftAssignment.CreatedBy,
                ShiftAssignment.CreatedAt,
                ShiftModel.Description.label("ShiftDescription"),
                ShiftDetailModel.DayIndexList,
            )
            .select_from(ShiftAssignment)
            .join(ShiftModel, ShiftAssignment.ShiftId == ShiftModel.Id)
            .join(
                ShiftDetailModel, ShiftAssignment.ShiftDetailId == ShiftDetailModel.Id
            )
            .order_by(ShiftAssignment.StartDate, ShiftAssignment.Id)
        ).all()
        app.logger.exception(f"getShiftAssignmentList thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": [dict(r) for r in shiftAssignmentList],
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
            "Description": f"Có lỗi ở máy chủ. Không thể truy cập được thông tin phân ca",
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
        shiftAssignment = db.session.execute(
            select(
                ShiftAssignmentType.Name.label("AssignmentTypeName"),
                ShiftAssignment,
                ShiftDetailModel,
            )
            .select_from(ShiftAssignment)
            .join(
                ShiftDetailModel,
                ShiftDetailModel.Id == ShiftAssignment.ShiftDetailId,
                isouter=True,
            )
            .where(
                and_(
                    ShiftAssignment.Id == id,
                    ShiftAssignment.AssignType == ShiftAssignmentType.Id,
                )
            )
        ).first()
        shiftAssignmentDetail = db.session.execute(
            select(
                ShiftAssignmentDetail.Id,
                ShiftAssignmentDetail.Target,
                ShiftAssignmentDetail.TargetType,
                case(
                    (ShiftAssignmentDetail.TargetType == 1, DepartmentModel.Name),
                    else_=EmployeeModel.LastName + " " + EmployeeModel.FirstName,
                ).label("TargetDescription"),
            )
            .select_from(ShiftAssignmentDetail)
            .join(
                DepartmentModel,
                and_(
                    ShiftAssignmentDetail.TargetType == 1,
                    ShiftAssignmentDetail.Target == DepartmentModel.Id,
                ),
                isouter=True,
            )
            .join(
                EmployeeModel,
                and_(
                    ShiftAssignmentDetail.TargetType == 2,
                    ShiftAssignmentDetail.Target == EmployeeModel.Id,
                ),
                isouter=True,
            )
            .where(
                and_(
                    ShiftAssignmentDetail.ShiftAssignmentId == id,
                    ShiftAssignmentDetail.Status == "1",
                )
            )
        ).all()
        detailDict = [dict(r) for r in shiftAssignmentDetail]
        response = {
            "Assignment": ShiftAssignmentSchema().dump(
                shiftAssignment["ShiftAssignment"],
            ),
            "ShiftDetail": ShiftDetailSchema().dump(
                shiftAssignment["ShiftDetailModel"]
            ),
        }
        response["Assignment"]["AssignmentTypeName"] = shiftAssignment[
            "AssignmentTypeName"
        ]
        response["AssignmentDetail"] = detailDict
        app.logger.info("getShiftAssignmentDetails thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": response,
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
            "Description": f"Có lỗi ở máy chủ. Không thể truy cập được thông tin phân ca",
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
        response = [dict(r) for r in shiftAssignmentTypeList]
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
            "Description": f"Có lỗi ở máy chủ. Không thể truy cập được thông tin kiểu phân ca.",
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

        # endregion

        assignmentId = jsonRequestData["Id"]
        description = (
            None
            if "Description" not in jsonRequestData
            else jsonRequestData["Description"]
        )
        note = None if "Note" not in jsonRequestData else jsonRequestData["Note"]
        assignType = (
            None
            if "AssignType" not in jsonRequestData
            else jsonRequestData["AssignType"]
        )
        departmentId = (
            None
            if "DepartmentId" not in jsonRequestData
            else jsonRequestData["DepartmentId"]
        )
        employeeId = (
            None
            if "EmployeeId" not in jsonRequestData
            else jsonRequestData["EmployeeId"]
        )
        data = db.session.execute(
            select(ShiftAssignment, ShiftDetailModel)
            .select_from(ShiftAssignment)
            .join(
                ShiftDetailModel, ShiftAssignment.ShiftDetailId == ShiftDetailModel.Id
            )
            .where(ShiftAssignment.Id == assignmentId)
        ).first()

        shiftAssignmentDetail = db.session.scalars(
            select(ShiftAssignmentDetail).where(
                and_(
                    ShiftAssignmentDetail.ShiftAssignmentId == assignmentId,
                    ShiftAssignmentDetail.TargetType == assignType,
                    ShiftAssignmentDetail.Status == "1",
                )
            )
        ).all()

        shiftAssignment = data["ShiftAssignment"]
        shiftDetail = data["ShiftDetailModel"]
        if description and description != shiftAssignment.Description:
            shiftAssignment.Description = description
        if note and note != shiftAssignment.Note:
            shiftAssignment.Note = note
        deleteArray = []
        insertArray = []
        if assignType == 1:  # Phân ca theo phòng ban vị trí
            deleteArray = list(
                filter(lambda x: (x.Target not in departmentId), shiftAssignmentDetail)
            )
            temp = list(map(lambda x: x.Target, shiftAssignmentDetail))
            temp2 = list(filter(lambda x: x not in temp, departmentId))
            insertArray = list(
                map(
                    lambda x: {
                        "ShiftAssignmentId": assignmentId,
                        "Target": x,
                        "TargetType": TargetType.Department.value,
                        "CreatedAt": datetime.now(),
                        "ModifiedAt": datetime.now(),
                        "CreatedBy": id,
                        "ModifiedBy": id,
                        "FinishAssignmentTime": shiftDetail.EndDate,
                    },
                    temp2,
                )
            )
        elif assignType == 2:  # Phân ca theo nhân viên
            deleteArray = list(
                filter(lambda x: (x.Target not in employeeId), shiftAssignmentDetail)
            )
            temp = list(map(lambda x: x.Target, shiftAssignmentDetail))
            temp2 = list(filter(lambda x: x not in temp, employeeId))
            insertArray = list(
                map(
                    lambda x: {
                        "ShiftAssignmentId": assignmentId,
                        "Target": x,
                        "TargetType": TargetType.Employee.value,
                        "CreatedAt": datetime.now(),
                        "ModifiedAt": datetime.now(),
                        "CreatedBy": id,
                        "ModifiedBy": id,
                        "FinishAssignmentTime": shiftDetail.EndDate,
                    },
                    temp2,
                )
            )
        else:
            raise ProjectException(f'Chưa hỗ trợ loại phân ca có mã "{assignType}"')
        if len(insertArray) + len(deleteArray) == 0:
            raise ProjectException("Không có sự thay đổi ở đối tượng được phân công.")
        if len(deleteArray) != 0:
            for x in deleteArray:
                x.Status = "0"
                x.ModifiedAt = datetime.now()
                x.ModifiedBy = id
            # db.session.execute(
            #     delete(ShiftAssignmentDetail).where(
            #         or_(*[ShiftAssignmentDetail.Id == x.Id for x in deleteArray])
            #     )
            # )
        if len(insertArray) != 0:
            db.session.execute(insert(ShiftAssignmentDetail), insertArray)
        db.session.commit()
        app.logger.info(f"UpdateAssignment [{assignmentId}] thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200
    except ProjectException as pEx:
        db.session.rollback()
        app.logger.exception(f"UpdateAssignment thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Không thể cập nhật được phân ca. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"UpdateAssignment thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Không thể cập nhật được phân ca.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info(f"UpdateAssignment kết thúc")
