from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request

from src.config import Config
from src.db import db
from src.extension import ProjectException
from src.jwt import get_jwt_identity, jwt_required
from src.employee.model import EmployeeModel, EmployeeInfoSchema, employeeInfoListSchema
from src.department.model import DepartmentModel, departmentListSchema

AttendanceMachineApi = Blueprint("attendance_machine", __name__)


# "GET", "POST" api/attendance_machine/department/load
@AttendanceMachineApi.route("/department/load", methods=["GET"])
def LoadDepartment():
    try:
        departmentList = DepartmentModel.query.all()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": departmentListSchema.dump(departmentList),
        }
    except ProjectException as pEx:
        app.logger.error(f"LoadDepartment thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.error(f"LoadDepartment thất bại. Có exception[{ex}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ. Đăng ký khuôn mặt không thành công",
            "ResponseData": None,
        }, 200


# "POST" api/attendance_machine/employee/load
@AttendanceMachineApi.route("/employee/load", methods=["POST"])
def LoadEmployeeList():
    try:
        # region Khai bao

        jsonRequest = request.get_json()
        print(jsonRequest)
        departmentId = (
            jsonRequest["DepartmentId"] if "DepartmentId" in jsonRequest else None
        )

        # endregion

        if departmentId:
            employeeList = EmployeeModel.query.filter(
                EmployeeModel.DepartmentId == departmentId
            ).all()
        else:
            employeeList = EmployeeModel.query.all()

        return {
            "Status": 1,
            "Description": None,
            "ResponseData": employeeInfoListSchema.dump(employeeList),
        }, 200
    except ProjectException as pEx:
        app.logger.error(f"LoadEmployeeList thất bại. Có exception[{str(pEx)}]")
        return {
            "Status": 0,
            "Description": f"{pEx}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.error(f"LoadEmployeeList thất bại. Có exception[{ex}]")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
