from flask import Blueprint, request, current_app as app
from src.db import db
from src.department.model import DepartmentModel, departmentSchema, departmentListSchema
from src.jwt import get_jwt_identity, jwt_required
from src.authentication.model import UserModel
from datetime import datetime

Department = Blueprint("department", __name__)


@Department.route("/list", methods=["GET"])
def GetDepartmentList():
    try:
        args = request.args.to_dict()
        page = 1
        perPage = 10
        if "Page" in args:
            page = int(args["Page"])
        if "PerPage" in args:
            perPage = int(args["PerPage"])
        departmentList = db.paginate(
            db.select(DepartmentModel).order_by(DepartmentModel.Id),
            page=page,
            per_page=perPage,
        )
        app.logger.info("GetDepartmentList successfully.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": departmentListSchema.dump(departmentList),
        }
    except Exception as ex:
        app.logger.info(f"GetDepartmentList thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Truy vấn danh sách phòng ban không thành công.",
            "ResponseData": None,
        }


@Department.route("/create", methods=["POST"])
@jwt_required()
def AddNewDepartment():
    try:
        jsonRequestData = request.get_json()

        # region validate

        email = get_jwt_identity()
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")

        if "Name" not in jsonRequestData or not jsonRequestData["Name"]:
            raise Exception("Invalid Name. Name is not found.")

        departmentName = jsonRequestData["Name"]
        user = db.session.execute(
            db.select(DepartmentModel).filter_by(Name=departmentName)
        ).scalar_one_or_none()

        if user:
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
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"AddNewDepartment thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Thêm phòng ban mới không thành công. {str(ex)}",
            "ResponseData": None,
        }


@Department.route("/update", methods=["PUT"])
@jwt_required()
def UpdateDepartment():
    try:
        jsonRequestData = request.get_json()

        # region validate

        email = get_jwt_identity()
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")
        if ("Id" not in jsonRequestData) or (not jsonRequestData["Id"]):
            raise Exception("Department Id is empty or invalid.")

        # endregion

        DepartmentId = jsonRequestData["Id"]
        department = db.session.execute(
            db.select(DepartmentModel).filter_by(Id=DepartmentId)
        ).scalar_one_or_none()
        if not department:
            raise Exception(f"Can not find employee id[{DepartmentId}]")
        hasSomeChanges = False
        for key in jsonRequestData:
            if getattr(department, key) != jsonRequestData[key]:
                hasSomeChanges = True
                setattr(department, key, jsonRequestData[key])
        if not hasSomeChanges:
            return {
                "Status": 1,
                "Description": f"Không có sự thay đổi nào trong dữ liệu của Phòng ban {DepartmentId}",
                "ResponseData": None,
            }
        department.ModifiedAt = datetime.now()
        department.ModifiedBy = user.Id
        db.session.commit()
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"UpdateDepartment thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Cập nhật phòng ban mới không thành công. {str(ex)}",
            "ResponseData": None,
        }
