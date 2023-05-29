from flask import Blueprint, current_app as app, request
from src.extension import ProjectException
from src.designation.model import (
    Designation as DesignationModel,
    designationSchema,
    designationListSchema,
    Status,
)
from src.db import db

Designation = Blueprint("designation", __name__)


@Designation.route("/list", methods=["GET"])
def GetDesignationList():
    try:
        designationList = db.session.execute(
            db.select(DesignationModel)
            .order_by(DesignationModel.Id)
            .where(DesignationModel.Status == Status.Active)
        ).scalars()
        response = designationListSchema.dump(designationList)
        return {
            "Status": 0,
            "Description": None,
            "ResponseData": response,
        }, 200
    except ProjectException as pEx:
        app.logger.exception(f"GetDesignationList thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"Không thể truy cập được thông tin vị trí. {pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.exception(f"GetDesignationList thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Không thể truy cập được thông tin vị trí.",
            "ResponseData": None,
        }, 200
