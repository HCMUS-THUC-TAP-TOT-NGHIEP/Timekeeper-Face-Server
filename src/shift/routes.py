import time
from datetime import datetime, time

from flask import Blueprint
from flask import current_app as app
from flask import request
from flask_json import json_response
from sqlalchemy import case, delete, func, insert, select

from src.authentication.model import UserModel
from src.db import db
from src.extension import ProjectException
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.admin_required import admin_required
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
)

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
                    (ShiftModel.Status == Status["Active"].value, "Đang sử dụng"),
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
    except Exception as ex:
        app.logger.error(f"GetShiftList thất bại. {ex}")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở server.",
            "ResponseData": None,
        }, 400


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
@jwt_required()
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
@jwt_required()
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
@jwt_required()
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
            None if "StartDate" not in jsonRequestData else jsonRequestData["StartDate"]
        )
        departmentList = (
            []
            if "DepartmentId" not in jsonRequestData
            else jsonRequestData["DepartmentId"]
        )
        designationList = (
            []
            if "DesignationId" not in jsonRequestData
            else jsonRequestData["DesignationId"]
        )
        note = "" if "Note" not in jsonRequestData else jsonRequestData["Note"]

        # endregion

        # region Thêm phân ca mới

        newShift = ShiftAssignment()
        newShift.Description = description
        newShift.AssignType = assignType
        newShift.ShiftId = shiftId
        newShift.StartDate = startDate
        newShift.EndDate = endDate
        newShift.Note = note
        newShift.CreatedBy = user.Id
        newShift.ModifiedBy = user.Id
        newShift.CreatedAt = datetime.now()
        newShift.ModifiedAt = datetime.now()

        # newShiftId = db.session.execute(
        #     insert(ShiftAssignment).values(newShift).returning(ShiftAssignment.Id)
        # )
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
        for designation in designationList:
            values.append(
                {
                    "Id": newShift.Id,
                    "Target": designation,
                    "TargetType": TargetType.Designation.value,
                    "CreatedAt": datetime.now(),
                    "ModifiedAt": datetime.now(),
                }
            )

        db.session.execute(insert(ShiftAssignmentDetail), values)

        # endregion

        db.session.commit()
        app.logger.info("AssignShift thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
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


@Shift.route("/assignment/detail", methods=["POST"])
@admin_required()
def getShiftAssignmentDetails():
    try:
        app.logger.info("getShiftAssignmentDetails thành công")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
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
