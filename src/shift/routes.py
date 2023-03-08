from datetime import datetime
from flask import Blueprint, current_app as app, request
from src.authentication.model import UserModel
from src.shift.model import ShiftModel, shiftListSchema
from src.db import db
from src.jwt import get_jwt_identity, jwt_required
from sqlalchemy import select, func

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
        shiftList = db.paginate(
            db.select(ShiftModel).order_by(ShiftModel.Id), page=page, per_page=perPage
        )
        app.logger.info(f"GetShiftList thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": shiftListSchema.dump(shiftList),
        }, 200
    except Exception as ex:
        app.logger.error(f"GetShiftList thất bại. {ex}")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở server.",
            "ResponseData": None,
        }, 400
