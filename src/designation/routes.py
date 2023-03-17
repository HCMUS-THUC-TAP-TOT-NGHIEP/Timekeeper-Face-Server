from flask import Blueprint, current_app as app, request
from src.extension import ProjectException
from src.designation.model import Designation, designationSchema, designationListSchema

Designation = Blueprint("designation", __name__)


@Designation.route("/list", methods=["GET"])
def GetDesignationList():
    try:
        designationList = Designation.query.all()
        return {
            "ResponseData": designationListSchema.dump(designationList),
        }, 200

    except ProjectException as pEx:
        pass
    except Exception as ex:
        pass
