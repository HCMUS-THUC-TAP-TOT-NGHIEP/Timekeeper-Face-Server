from flask import Blueprint, request, jsonify, current_app as app
from src.jwt import (
    jwt_required,
    get_jwt_identity,
)
from src.employee.model import EmployeeModel, employeeInfoListSchema, employeeInfoSchema
from src.authentication.model import UserModel
from src.db import db
from datetime import datetime
from src.extension import object_as_dict

Employee = Blueprint("employee", __name__)


# GET api/employee
@Employee.route("/", methods=["GET"])
@jwt_required()
def GetEmployeeInfo():
    try:
        email = get_jwt_identity()
        employeeId = request.args.get("Id")
        print(type(employeeId))
        employee = db.session.execute(
            db.select(EmployeeModel).filter_by(Id=employeeId)
        ).scalar_one()
        if not employee:
            raise Exception(f"Employee {employeeId} not found.")
        app.logger.info(f"GetEmployeeInfo Id[{employeeId}] thành công.")
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": employeeInfoSchema.dump(employee),
        }
    except Exception as ex:
        app.logger.exception(
            f"GetEmployeeInfo Id[{employeeId}] thất bại. Có exception[{str(ex)}]"
        )
        return {
            "Status": 0,
            "Description": f"Try vấn thông tin nhân viên không thành công.",
            "ResponseData": None,
        }


# POST api/employee/create
@Employee.route("/create", methods=["POST"])
@jwt_required()
def CreateEmployee():
    try:
        jsonRequestData = request.get_json()
        firstName = jsonRequestData["FirstName"]
        lastName = jsonRequestData["LastName"]
        dateOfBirthStr = jsonRequestData["DateOfBirth"]
        genderStr = jsonRequestData["Gender"]
        address = jsonRequestData["Address"]
        joinDateStr = jsonRequestData["JoinDate"]
        email = get_jwt_identity()

        # region validate

        if not isinstance(firstName, str) or not firstName or not firstName.strip():
            raise Exception(
                "Invalid first name. First name is empty or blank or not string"
            )
        if not isinstance(lastName, str) or not lastName or not lastName.strip():
            raise Exception(
                "Invalid last name. Last name is empty or blank or not string"
            )
        if not isinstance(address, str) or not address or not address.strip():
            raise Exception("Invalid address. Address is empty or blank or not string")

        # endregion

        newEmployee = EmployeeModel()
        newEmployee.FirstName = firstName
        newEmployee.LastName = lastName
        newEmployee.Address = address
        newEmployee.Gender = genderStr
        newEmployee.JoinDate = joinDateStr
        newEmployee.DateOfBirth = dateOfBirthStr
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one()
        newEmployee.CreatedBy = user.Id
        newEmployee.CreatedAt = datetime.now()
        newEmployee.ModifiedBy = user.Id
        newEmployee.ModifiedAt = datetime.now()
        db.session.add(newEmployee)
        db.session.commit()
        print(newEmployee)
        return {
            "Status": 1,
            "Description": f"Thêm nhân viên mới thành công.",
            "ResponseData": {"Id": newEmployee.Id},
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Thêm nhân viên mới không thành công. Có lỗi {str(ex)}",
            "ResponseData": None,
        }


# PUT api/employee/update
@Employee.route("/update", methods=["PUT"])
@jwt_required()
def UpdateEmployeeInfo():
    try:
        email = get_jwt_identity()
        jsonRequestData = request.get_json()
        EmployeeId = jsonRequestData["Id"]
        # region validate

        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")
        if not EmployeeId:
            raise Exception("Employee Id is empty or invalid.")

        # endregion

        employeeInfo = db.session.execute(
            db.select(EmployeeModel).filter_by(Id=EmployeeId)
        ).scalar_one_or_none()
        if not employeeInfo:
            raise Exception(f"Can not find employee id[{EmployeeId}]")
        employeeInfoDict = object_as_dict(employeeInfo)
        hasSomeChanges = False
        for key in jsonRequestData:
            if key not in employeeInfoDict:
                raise Exception(f"Cannot found key {key} in {employeeInfoDict}")
            if employeeInfoDict[key] != jsonRequestData[key]:
                hasSomeChanges = True
                employeeInfoDict[key] = jsonRequestData[key]
        if not hasSomeChanges:
            return {
                "Status": 1,
                "Description": f"Không có sự thay đổi nào trong dữ liệu của Nhân viên {employeeInfo.Id}",
                "ResponseData": None,
            }
        employeeInfo = EmployeeModel(**employeeInfoDict)
        employeeInfo.ModifiedAt = datetime.now()
        employeeInfo.ModifiedBy = user.Id
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.info(
            f"UpdateEmployeeInfo Id[{EmployeeId}] thất bại. Có exception[{str(ex)}]"
        )
        return {
            "Status": 0,
            "Description": f"Chỉnh sửa thông tin nhân viên không thành công.",
            "ResponseData": None,
        }


# DELETE api/employee/
@Employee.route("/", methods=["DELETE"])
@jwt_required()
def DeleteEmployee():
    try:
        jsonRequestData = request.get_json()
        employeeId = jsonRequestData["EmployeeId"]

        # region validate

        if not employeeId:
            raise Exception("Employee Id is empty or invalid.")

        # endregion
        employee = db.session.execute(
            db.select(EmployeeModel).filter_by(Id=employeeId)
        ).scalar_one()
        print(employee)
        if not employee:
            raise Exception("Could not find employee with id: %s" % employeeId)
        db.session.delete(employee)
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Delete Unsucessfully. Có lỗi {str(ex)}",
            "ResponseData": None,
        }
