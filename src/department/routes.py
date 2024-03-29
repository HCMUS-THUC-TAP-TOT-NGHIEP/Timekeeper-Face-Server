import json
from datetime import datetime

from flask import Blueprint
from flask import current_app as app
from flask import request
from sqlalchemy import func, select

from src.authentication.model import UserModel
from src.db import db
from src.department.model import DepartmentModel, departmentListSchema, departmentSchema, vDepartment
from src.employee.model import EmployeeModel, employeeInfoListSchema
from src.utils.extension import object_as_dict
from src.jwt import get_jwt_identity, jwt_required
from src.middlewares.token_required import admin_required
from src.utils.extension import ProjectException

Department = Blueprint("department", __name__)

# api/department/list


@Department.route("/list", methods=["GET"])
@admin_required()
def GetDepartmentList():
    try:
        args = request.args.to_dict()
        page = None
        perPage = None
        if "Page" in args:
            page = int(args["Page"])
        if "PerPage" in args:
            perPage = int(args["PerPage"])
        query = select(vDepartment)
        if page and perPage:
            data = db.paginate(query, page=page, per_page=perPage)
            departmentList = departmentListSchema.dump(data.items)
            total = data.total
            app.logger.info("GetDepartmentList successfully.")
            return {
                "Status": 1,
                "Description": None,
                "ResponseData": {
                    "DepartmentList": departmentList,
                    "Total": total,
                }
            }, 200
        data = db.session.execute(query).scalars()
        departmentList = departmentListSchema.dump(data)
        app.logger.info("GetDepartmentList successfully.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {
                "DepartmentList": departmentList,
                "Total": len(departmentList)
            },
        }, 200

    except Exception as ex:
        app.logger.info(
            f"GetDepartmentList thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200


@Department.route("/create", methods=["POST"])
@admin_required()
def AddNewDepartment():
    try:
        jsonRequestData = request.get_json()

        # region validate

        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")

        if "Name" not in jsonRequestData or not jsonRequestData["Name"]:
            raise Exception("Invalid Name. Name is not found.")

        departmentName = jsonRequestData["Name"]
        department = db.session.execute(
            db.select(DepartmentModel).filter_by(Name=departmentName)
        ).scalar_one_or_none()

        if department:
            raise Exception(f"Phòng ban {departmentName} đã tồn tại.")

        # endregion

        managerId = (
            jsonRequestData["ManagerId"] if "ManagerId" in jsonRequestData else None
        )
        newDepartment = DepartmentModel()
        newDepartment.Name = departmentName
        newDepartment.ManagerId = managerId
        newDepartment.CreatedAt = datetime.now()
        newDepartment.CreatedBy = user.Id
        newDepartment.ModifiedAt = datetime.now()
        newDepartment.ModifiedBy = user.Id
        newDepartment.Status = "1"
        db.session.add(newDepartment)
        db.session.commit()
        app.logger.info(f"AddNewDepartment thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": {"Id": newDepartment.Id},
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"AddNewDepartment thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Thêm phòng ban mới không thành công. {str(ex)}",
            "ResponseData": None,
        }, 200


@Department.route("/update", methods=["PUT"])
@admin_required()
def UpdateDepartment():
    try:
        jsonRequestData = request.get_json()

        # region validate

        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")
        if ("Id" not in jsonRequestData) or (not jsonRequestData["Id"]):
            raise Exception("Department Id is empty or invalid.")

        # endregion

        DepartmentId = jsonRequestData["Id"]
        name = jsonRequestData["Name"] if "Name" in jsonRequestData else None
        managerId = jsonRequestData["ManagerId"] if "ManagerId" in jsonRequestData else None
        status = jsonRequestData["Status"] if "Status" in jsonRequestData else None
        department = DepartmentModel.query.filter_by(Id=DepartmentId).first()
        if not department:
            raise ProjectException(f"Can not find employee id[{DepartmentId}]")

        if name and name != department.Name:
            department.Name = name
        employee = EmployeeModel.query.filter_by(Id=managerId).first()
        if employee:
            employee.DepartmentId = DepartmentId
        if managerId and managerId != department.ManagerId:
            department.ManagerId = managerId
        if isinstance(status, int) and status != department.Status:
            department.Status = status

        department.ModifiedAt = datetime.now()
        department.ModifiedBy = user.Id
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"UpdateDepartment thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Cập nhật phòng ban mới không thành công. {str(ex)}",
            "ResponseData": None,
        }


@Department.route("/", methods=["DELETE"])
@admin_required()
def DeleteOneDepartment():
    try:
        jsonRequestData = request.get_json()

        # region validate

        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            app.logger.error(
                "DeleteOneDepartment thất bại. Không tìm thấy user có email [{email}]."
            )
            return {
                "Status": 0,
                "Description": f"User [{email}] không tồn tại",
                "ResponseData": None,
            }, 401
        if "Id" not in jsonRequestData or not isinstance(jsonRequestData["Id"], int):
            app.logger.error(
                "DeleteOneDepartment thất bại. Không tìm mã phòng ban trong request body data."
            )
            return {
                "Status": 0,
                "Description": f"Không tìm thấy mã phòng ban trong request.",
                "ResponseData": None,
            }, 400

        # endregion

        departmentId = jsonRequestData["Id"]
        department = db.session.execute(
            db.select(DepartmentModel).filter_by(Id=departmentId)
        ).scalar_one_or_none()
        if not department:
            app.logger.error(
                "DeleteOneDepartment thất bại. Không tìm thấy phòng ban có mã {departmentId}."
            )
            return {
                "Status": 0,
                "Description": f"Không tìm thấy phòng ban có mã {departmentId}.",
                "ResponseData": None,
            }, 400
        print(departmentSchema.dump(department))
        db.session.delete(department)
        db.session.commit()
        app.logger.info(
            f"DeleteOneDepartment Id[{departmentId}] thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.error(f"DeleteOneDepartment thất bại. {ex}")
        return {
            "Status": 0,
            "Description": f"Có lỗi ở server.",
            "ResponseData": None,
        }, 400
