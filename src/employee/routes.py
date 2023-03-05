from datetime import datetime
from flask import Blueprint,current_app as app, request
from src.authentication.model import UserModel
from src.db import db
from src.employee.model import (EmployeeModel, employeeInfoListSchema,
                                employeeInfoSchema)
from src.jwt import get_jwt_identity, jwt_required

Employee = Blueprint("employee", __name__)


# GET api/employee
@Employee.route("/", methods=["GET"])
@jwt_required()
def GetEmployeeInfo():
    try:
        email = get_jwt_identity()
        employeeId = request.args.get("Id")
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
        email = get_jwt_identity()

        # region validate

        if "FirstName" not in jsonRequestData:
            raise Exception("Invalid first name. First name is not found.")
        if "LastName" not in jsonRequestData:
            raise Exception("Invalid Last name. Last name is not found.")
        if "DateOfBirth" not in jsonRequestData:
            raise Exception("Invalid Date Of Birth. Date Of Birth is not found.")
        if "Gender" not in jsonRequestData:
            raise Exception("Invalid Gender. Gender is not found.")
        if "Address" not in jsonRequestData:
            raise Exception("Invalid Address. Address is not found.")
        if "JoinDate" not in jsonRequestData:
            raise Exception("Invalid Gender. JoinDate is not found.")
        if "Email" not in jsonRequestData:
            raise Exception("Invalid Email. Email is not found.")
        if "MobilePhone" not in jsonRequestData:
            raise Exception("Invalid MobilePhone. MobilePhone is not found.")
        if "DepartmentId" not in jsonRequestData:
            raise Exception("Invalid DepartmentId. DepartmentId is not found.")

        firstName = jsonRequestData["FirstName"]
        lastName = jsonRequestData["LastName"]
        dateOfBirthStr = jsonRequestData["DateOfBirth"]
        genderStr = jsonRequestData["Gender"]
        address = jsonRequestData["Address"]
        joinDateStr = jsonRequestData["JoinDate"]
        Position = jsonRequestData["Position"]
        Email = jsonRequestData["Email"]
        MobilePhone = jsonRequestData["MobilePhone"]
        DepartmentId = jsonRequestData["DepartmentId"]

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
        newEmployee.Position = Position
        newEmployee.Email = Email
        newEmployee.MobilePhone = MobilePhone
        newEmployee.DepartmentId = DepartmentId
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one()
        newEmployee.CreatedBy = user.Id
        newEmployee.CreatedAt = datetime.now()
        newEmployee.ModifiedBy = user.Id
        newEmployee.ModifiedAt = datetime.now()
        db.session.add(newEmployee)
        db.session.commit()
        app.logger.info(f"CreateEmployee thành công.")
        return {
            "Status": 1,
            "Description": f"Thêm nhân viên mới thành công.",
            "ResponseData": {"Id": newEmployee.Id},
        }
    except Exception as ex:
        db.session.rollback()
        app.logger.exception(f"CreateEmployee thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Thêm nhân viên mới không thành công.",
            "ResponseData": None,
        }


# PUT api/employee/update
@Employee.route("/update", methods=["PUT"])
@jwt_required()
def UpdateEmployeeInfo():
    try:
        email = get_jwt_identity()
        jsonRequestData = request.get_json()

        # region validate

        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")
        if ("Id" not in jsonRequestData) or (not jsonRequestData["Id"]):
            raise Exception("Employee Id is empty or invalid.")

        # endregion

        EmployeeId = jsonRequestData["Id"]

        employeeInfo = db.session.execute(
            db.select(EmployeeModel).filter_by(Id=EmployeeId)
        ).scalar_one_or_none()
        if not employeeInfo:
            raise Exception(f"Can not find employee id[{EmployeeId}]")
        hasSomeChanges = False

        for key in jsonRequestData:
            if getattr(employeeInfo, key) != jsonRequestData[key]:
                hasSomeChanges = True
                setattr(employeeInfo, key, jsonRequestData[key])
        if not hasSomeChanges:
            return {
                "Status": 1,
                "Description": f"Không có sự thay đổi nào trong dữ liệu của Nhân viên {employeeInfo.Id}",
                "ResponseData": None,
            }
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

        # region validate
        email = get_jwt_identity()
        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")
        if ("EmployeeId" not in jsonRequestData) or (not jsonRequestData["EmployeeId"]):
            raise Exception("Employee Id is empty or invalid.")

        # endregion
        employeeId = jsonRequestData["EmployeeId"]
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


# GET api/employee/many
@Employee.route("/many", methods=["GET"])
@jwt_required()
def GetManyEMployee():
    try:
        email = get_jwt_identity()
        args = request.args.to_dict()
        page = 1
        perPage = 10
        # region validate

        user = db.session.execute(
            db.select(UserModel).filter_by(EmailAddress=email)
        ).scalar_one_or_none()
        if not user:
            raise Exception(f"No account found for email address[{email}]")
        # endregion

        if "Page" in args:
            page = args["Page"]
        if "PerPage" in args:
            perPage = args["PerPage"]
        employees = db.paginate(
            db.select(EmployeeModel).order_by(EmployeeModel.Id, EmployeeModel.JoinDate)
        )
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": employeeInfoListSchema.dump(employees),
        }
    except Exception as ex:
        app.logger.info(f"GetManyEMployee thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Truy vấn danh sách nhân viên không thành công.",
            "ResponseData": None,
        }
