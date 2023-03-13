from datetime import datetime
from flask import Blueprint, current_app as app, request
from src.authentication.model import UserModel
from src.shift.model import (
    ShiftModel,
    shiftListSchema,
    ShiftTypeModel,
    shiftListResponseSchema,
    ShiftTypeModelSchema,
)
from src.db import db
from src.jwt import get_jwt_identity, jwt_required
from sqlalchemy import select, func, case, delete
from flask_json import json_response
from datetime import time
from enum import Enum
from src.extension import ProjectException
import time
from datetime import datetime

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


Status = Enum("Status", ["Active", "Inactive"])
