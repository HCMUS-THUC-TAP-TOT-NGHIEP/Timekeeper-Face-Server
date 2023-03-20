import time
from datetime import datetime, time

from flask import Blueprint
from flask import current_app as app
from flask import request
from flask_json import json_response
from sqlalchemy import case, delete, func, insert, select, and_

from src.authentication.model import UserModel
from src.db import db
from src.extension import ProjectException
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.shift.model import (
    ShiftAssignment,
    ShiftAssignmentDetail,
    ShiftAssignmentSchema,
    ShiftModel,
    ShiftTypeModel,
    ShiftTypeModelSchema,
    Status,
    TargetType,
    shiftListResponseSchema,
    shiftListSchema,
    ShiftAssignmentType,
)
from src.department.model import DepartmentModel
from src.designation.model import Designation
from src.employee.model import EmployeeModel

Shift = Blueprint("shift", __name__)


@Shift.route("/list", methods=["GET"])
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
                ShiftModel.StartTime,
                ShiftModel.FinishTime,
                ShiftModel.BreakAt,
                ShiftModel.BreakEnd,
                ShiftModel.Type,
                ShiftTypeModel.Description.label("TypeText"),
                ShiftModel.Status,
                case(
                    (ShiftModel.Status == Status.Active, "Đang sử dụng"),
                    else_="Inactive",
                ).label("StatusText"),
            )
            .select_from(ShiftModel)
            .join(
                ShiftTypeModel,
                ShiftModel.Type == ShiftTypeModel.Id,
                isouter=True,
            )
            .order_by(ShiftModel.Id)
        ).all()

        app.logger.info(f"GetShiftList thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": shiftListResponseSchema.dump(shiftList),
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


@Shift.route("/type/list", methods=["GET"])
def GetShiftTypeList():
    try:
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


@Shift.route("/create", methods=["POST"])
@admin_required()
def createNewShift():
    try:
        jsonRequestData = request.get_json()
        email = get_jwt_identity()

        # region validate
        if "Description" not in jsonRequestData:
            raise ProjectException("Không tìm thấy tên ca làm việc")
        if "ShiftType" not in jsonRequestData:
            raise ProjectException("Không tìm thấy loại ca làm việc")
        if "StartTime" not in jsonRequestData:
            raise ProjectException("Không tìm thấy giờ checkin")
        if "FinishTime" not in jsonRequestData:
            raise ProjectException("Không tìm thấy giờ checkout")
        # if "BreakAt" not in jsonRequestData:
        #     raise ProjectException("Không tìm thấy tên ca làm việc")
        # if "BreakEnd" not in jsonRequestData:
        #     raise ProjectException("Không tìm thấy tên ca làm việc")
        # if "Status" not in jsonRequestData:
        #     raise ProjectException("Không tìm thấy tên ca làm việc")

        # endregion

        Description = jsonRequestData["Description"]
        ShiftType = jsonRequestData["ShiftType"]
        StartTime = jsonRequestData["StartTime"]
        FinishTime = jsonRequestData["FinishTime"]
        BreakAt = jsonRequestData["BreakAt"]
        BreakEnd = jsonRequestData["BreakEnd"]
        # Status = jsonRequestData["Status"]

        newShift = ShiftModel()
        newShift.Description = Description
        newShift.StartTime = StartTime
        newShift.FinishTime = FinishTime
        newShift.BreakAt = BreakAt
        newShift.BreakEnd = BreakEnd
        newShift.Status = 1
        newShift.Type = ShiftType
        newShift.CreatedAt = datetime.now()
        newShift.ModifiedAt = datetime.now()
        newShift.CreatedBy = 0
        newShift.ModifiedBy = 0
        db.session.add(newShift)
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


@Shift.route("/", methods=["DELETE"])
@admin_required()
def deleteShift():
    try:
        jsonRequestData = request.get_json()
        email = get_jwt_identity()

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


@Shift.route("/update", methods=["PUT"])
@admin_required()
def updateShift():
    try:
        jsonRequestData = request.get_json()
        email = get_jwt_identity()

        # region validate

        if "Id" not in jsonRequestData:
            raise ProjectException("Không tìm thấy mã ca làm việc trong request.")

        # endregion

        shiftId = jsonRequestData["Id"]
        shift = db.session.execute(
            db.select(ShiftModel).filter_by(Id=shiftId)
        ).scalar_one_or_none()

        if not shift:
            raise ProjectException(f"Không tồn tại ca làm việc Id [{shiftId}]")
        hasSomeChanges = False

        for key in jsonRequestData:
            if getattr(shift, key) != jsonRequestData[key]:
                hasSomeChanges = True
                setattr(shift, key, jsonRequestData[key])
        if not hasSomeChanges:
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


@Shift.route("/assignment", methods=["POST"])
@admin_required()
def AssignShift():
    try:
        jsonRequestData = request.get_json()
        email = get_jwt_identity()
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
        if "StartDate" not in jsonRequestData:
            raise ProjectException("Máy chủ không tìm thấy ngày bắt đầu.")

        # endregion

        # region Khai báo

        description = jsonRequestData["Description"]
        assignType = jsonRequestData["AssignType"]
        shiftId = jsonRequestData["ShiftId"]
        startDate = jsonRequestData["StartDate"]
        endDate = (
            None if "EndDate" not in jsonRequestData else jsonRequestData["EndDate"]
        )
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

        # region Thêm phân ca mới

        newShift = ShiftAssignment()
        newShift.Description = description
        newShift.AssignType = assignType
        newShift.ShiftId = shiftId
        newShift.StartDate = datetime.strptime(startDate, "%Y-%m-%d")
        newShift.EndDate = datetime.strptime(endDate, "%Y-%m-%d")
        newShift.Note = note
        newShift.CreatedBy = user.Id
        newShift.ModifiedBy = user.Id
        newShift.CreatedAt = datetime.now()
        newShift.ModifiedAt = datetime.now()
        db.session.add(newShift)
        db.session.flush()
        db.session.refresh(newShift)

        # endregion

        # region Thêm chi tiết phân ca mới

        values = []
        for department in departmentList:
            values.append(
                {
                    "Id": newShift.Id,
                    "Target": department,
                    "TargetType": TargetType.Department.value,
                    "CreatedAt": datetime.now(),
                    "ModifiedAt": datetime.now(),
                }
            )
        for employee in employeeList:
            values.append(
                {
                    "Id": newShift.Id,
                    "Target": employee,
                    "TargetType": TargetType.Designation.value,
                    "CreatedAt": datetime.now(),
                    "ModifiedAt": datetime.now(),
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

        db.session.commit()
        app.logger.info("AssignShift thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"Id": newShift.Id},
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


@Shift.route("/assignment/list", methods=["GET"])
@admin_required()
def getShiftAssignmentList():
    try:
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
            )
            .select_from(ShiftAssignment)
            .join(ShiftModel, ShiftAssignment.ShiftId == ShiftModel.Id)
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


@Shift.route("/assignment/detail", methods=["POST"])
@admin_required()
def getShiftAssignmentDetail():
    try:
        jsonRequestData = request.get_json()

        # region validate

        if "Id" not in jsonRequestData:
            raise ProjectException("Không tìm thấy thông tin mã phân ca")

        # endregion

        id = jsonRequestData["Id"]
        shiftAssignment = db.session.execute(
            select(
                ShiftAssignment.Id,
                ShiftAssignment.ShiftId,
                ShiftAssignment.StartDate,
                ShiftAssignment.EndDate,
                ShiftAssignment.Note,
                ShiftAssignment.Description,
                ShiftAssignment.CreatedAt,
                ShiftAssignment.CreatedBy,
                ShiftAssignment.AssignType,
                ShiftAssignmentType.Name.label("AssignmentTypeName"),
            ).where(
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
                    else_=EmployeeModel.FirstName + " " + EmployeeModel.LastName,
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
            .where(ShiftAssignmentDetail.Id == id)
        ).all()
        detailDict = [dict(r) for r in shiftAssignmentDetail]
        response = ShiftAssignmentSchema().dump(shiftAssignment)
        response["Detail"] = detailDict
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


@Shift.route("/assignment/all-type", methods=["GET", "POST"])
@jwt_required()
def GetAssignmentTypes():
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
