from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request

from src.config import Config
from src.db import db
from src.utils.extension import ProjectException
from src.jwt import get_jwt_identity, jwt_required 
from src.middlewares.token_required import admin_required
from src.employee.model import EmployeeModel, EmployeeSchema, employeeInfoListSchema
from src.department.model import DepartmentModel, departmentListSchema
from sqlalchemy import or_, func, String

AttendanceMachineApi = Blueprint("attendance_machine", __name__)


# "GET", "POST" api/attendance_machine/department/load
@AttendanceMachineApi.route("/department/load", methods=["GET"])
@admin_required()
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
            "Description": f"Xảy ra lỗi ở máy chủ. Đăng ký khuôn mặt không thành công",
            "ResponseData": None,
        }, 200


# "POST" api/attendance_machine/employee/load
@AttendanceMachineApi.route("/employee/load", methods=["POST"])
@admin_required()
def LoadEmployeeList():
    try:
        # region Khai bao

        jsonRequest = request.get_json()
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
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200

# "POST" api/attendance_machine/employee/load2
@AttendanceMachineApi.route("/employee/load2", methods=["POST"])
def LoadEmployeeList2():
    try:
        app.logger.info("LoadEmployeeList2 bắt đầu")
        # region Khai bao

        jsonRequest = request.get_json()
        Keyword = (
            jsonRequest["Keyword"] if "Keyword" in jsonRequest else None
        )

        # endregion

        if Keyword:
            Keyword = Keyword.strip().lower()
            employeeList = EmployeeModel.query.filter(
                or_(
                func.lower(func.cast(EmployeeModel.Id, String)).like("%" + Keyword + '%'),
                func.lower(EmployeeModel.FirstName).like("%" + Keyword + '%'),
                func.lower(EmployeeModel.LastName).like("%" + Keyword + '%')
                )
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
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
