from datetime import datetime
import io
import mimetypes
from flask import Blueprint, send_file, send_from_directory
from flask import current_app as app
from flask import request
import pandas
from sqlalchemy import select
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename

from src.authentication.model import UserModel
from src.db import db
from src.department.model import DepartmentModel
from src.employee.model import (EmployeeModel, employeeInfoListSchema, vEmployeeModel,
                                employeeInfoSchema)
from src.utils.extension import ProjectException
from src.jwt import get_jwt_identity, jwt_required, get_jwt
from src.middlewares.token_required import admin_required
import numpy as np
from os import path, curdir
from sqlalchemy import or_, func, String
Employee = Blueprint("employee", __name__)
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# GET api/employee
@Employee.route("/", methods=["GET"])
@jwt_required()
def GetEmployeeInfo():
    try:
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]

        employeeId = request.args.get("Id")
        employee = vEmployeeModel.query.filter_by(Id=employeeId).first()

        if not employee:
            raise Exception(f"Employee {employeeId} not found.")

        app.logger.info(f"GetEmployeeInfo Id[{employeeId}] thành công.")

        return {
            "Status": 1,
            "Description": None,
            "ResponseData": employeeInfoSchema.dump(employee),
        }, 200

    except Exception as ex:
        app.logger.exception(
            f"GetEmployeeInfo Id[{employeeId}] thất bại. Có exception[{str(ex)}]"
        )
        return {
            "Status": 0,
            "Description": f"Try vấn thông tin nhân viên không thành công.",
            "ResponseData": None,

        }, 200

# POST api/employee/create
@Employee.route("/create", methods=["POST"])
@jwt_required()
def CreateEmployee():

    try:
        jsonRequestData = request.get_json()
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]

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
        firstName = jsonRequestData["FirstName"]
        lastName = jsonRequestData["LastName"]
        dateOfBirthStr = jsonRequestData["DateOfBirth"]
        genderStr = jsonRequestData["Gender"]
        address = jsonRequestData["Address"]
        joinDateStr = jsonRequestData["JoinDate"]
        Position = jsonRequestData["Position"]
        Email = jsonRequestData["Email"]
        MobilePhone = jsonRequestData["MobilePhone"]
        DepartmentId = jsonRequestData["DepartmentId"] if "DepartmentId" in jsonRequestData else None
        if not isinstance(firstName, str) or not firstName or not firstName.strip():
            raise Exception(
                "Invalid first name. First name is empty or blank or not string"
            )
        if not isinstance(lastName, str) or not lastName or not lastName.strip():
            raise Exception(
                "Invalid last name. Last name is empty or blank or not string"
            )
        if not isinstance(address, str) or not address or not address.strip():
            raise Exception(
                "Invalid address. Address is empty or blank or not string")

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
        }, 200

    except Exception as ex:
        db.session.rollback()
        app.logger.exception(
            f"CreateEmployee thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Thêm nhân viên mới không thành công.",
            "ResponseData": None,
        }, 200

# PUT api/employee/update
@Employee.route("/update", methods=["PUT"])
@jwt_required()
def UpdateEmployeeInfo():
    try:
        identity = get_jwt_identity()
        email = identity["email"]
        username = identity["username"]
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
        if 'FirstName' in jsonRequestData:
            employeeInfo.FirstName = jsonRequestData["FirstName"]
        if 'LastName' in jsonRequestData:
            employeeInfo.LastName = jsonRequestData["LastName"]
        if 'Email' in jsonRequestData:
            employeeInfo.Email = jsonRequestData["Email"]
        if 'MobilePhone' in jsonRequestData:
            employeeInfo.MobilePhone = jsonRequestData["MobilePhone"]
        if 'DateOfBirth' in jsonRequestData:
            employeeInfo.DateOfBirth = jsonRequestData["DateOfBirth"]
        if 'Gender' in jsonRequestData:
            employeeInfo.Gender = jsonRequestData["Gender"]
        if 'JoinDate' in jsonRequestData:
            employeeInfo.JoinDate = jsonRequestData["JoinDate"]
        if 'LeaveDate' in jsonRequestData:
            employeeInfo.LeaveDate = jsonRequestData["LeaveDate"]
        if 'DepartmentId' in jsonRequestData:
            if employeeInfo.DepartmentId is None:
                employeeInfo.DepartmentId = int(jsonRequestData["DepartmentId"])
            elif employeeInfo.DepartmentId != int(jsonRequestData["DepartmentId"]):
                current_department = DepartmentModel.query.filer_by(Id=employeeInfo.DepartmentId).first()
                new_department = DepartmentModel.query.filer_by(Id=int(jsonRequestData["DepartmentId"])).first()
                if new_department:
                    employeeInfo.DepartmentId = new_department.Id
                if current_department and current_department.ManagerId == employeeInfo.Id:
                    current_department.ManagerId = None
        if 'Position' in jsonRequestData:
            employeeInfo.Position = jsonRequestData['Position']
        employeeInfo.ModifiedAt = datetime.now()
        employeeInfo.ModifiedBy = user.Id
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200

    except Exception as ex:
        db.session.rollback()
        app.logger.info(
            f"UpdateEmployeeInfo Id[{EmployeeId}] thất bại. Có exception[{str(ex)}]"
        )
        return {
            "Status": 0,
            "Description": f"Chỉnh sửa thông tin nhân viên không thành công.",
            "ResponseData": None,
        }, 200

# DELETE api/employee/
@Employee.route("/", methods=["DELETE"])
@jwt_required()
def DeleteEmployee():
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

        if ("EmployeeId" not in jsonRequestData) or (not jsonRequestData["EmployeeId"]):
            raise Exception("Employee Id is empty or invalid.")

        # endregion

        employeeId = jsonRequestData["EmployeeId"]
        employee = db.session.execute(
            db.select(EmployeeModel).filter_by(Id=employeeId)
        ).scalar_one()
        if not employee:
            raise Exception("Could not find employee with id: %s" % employeeId)

        db.session.delete(employee)
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None,
        }, 200

    except Exception as ex:
        db.session.rollback()
        app.logger.exception(ex)
        return {
            "Status": 0,
            "Description": f"Delete Unsucessfully. Có lỗi {str(ex)}",
            "ResponseData": None,
        }, 200

# GET api/employee/many
@Employee.route("/many", methods=["GET", "POST"])
@admin_required()
def GetManyEmployee():
    try:
        args = request.args.to_dict()
        perPage = int(args["PerPage"]) if "PerPage" in args else 10
        page = int(args["Page"]) if "Page" in args else 1
        searchString = args["SearchString"] if "SearchString" in args else ""
        query = db.select(vEmployeeModel)
        if searchString and searchString.strip():
            sqlStr = "%" + searchString.upper() + "%"
            query = query.where(or_(func.cast(vEmployeeModel.Id, String).like(sqlStr),
                                    func.concat(func.upper(vEmployeeModel.LastName)," ", func.upper(vEmployeeModel.FirstName)).like(sqlStr)))
        if request.method == "GET":
            result = db.paginate(
                query,
                # db.select(vEmployeeModel)
                # .order_by(vEmployeeModel.Id),
                per_page=perPage,
                page=page
            )
            employees = employeeInfoListSchema.dump(result.items)
            return {
                "Status": 1,
                "Description": None,
                "ResponseData": {
                    "EmployeeList": employees,
                    "Total": result.total
                },
            }, 200
        if request.method == "POST":
            jsonRequestData = request.get_json()
            department = jsonRequestData["Department"] if "Department" in jsonRequestData else None
            result = EmployeeModel.GetEmployeeList(department=[department] if department else None, name=searchString)
            return {
                "Status": 1,
                "Description": None,
                "ResponseData": result,
            }, 200
    except Exception as ex:
        app.logger.info(
            f"GetManyEmployee thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ. Hãy kiễm tra log.",
            "ResponseData": None,
        }, 200

# POST api/employee/import
@Employee.route("/import", methods=["POST"])
@admin_required()
def importData():
    try:
        app.logger.info("Importing EmployeeModel start")
        identity = get_jwt_identity()
        claims = get_jwt()
        id = claims["id"]
        email = identity["email"]
        username = identity["username"]
        fileRequest = request.files["ImportData"]

        # region validate

        if not fileRequest:
            raise ProjectException("Không tìm thấy tệp tin")
        if not CheckIfFileAllowed(fileRequest.filename):
            raise ProjectException(
                f"Tập tin {fileRequest.filename} có định dạng không phù hợp (cần phải là {string.join(ALLOWED_EXTENSIONS)}) ")

        # endregion

        data = list()

        filename = secure_filename(fileRequest.filename)
        fileExtension = GetFileExtensionFromFileNam(filename)
        if fileExtension in ['xlsx', 'xls']:
            excel_data = pandas.read_excel(
                fileRequest, sheet_name="Data", header=3)
            if (excel_data.empty):
                raise ProjectException("Không có dữ liệu.")
            rowCount = len(excel_data.index)
            colCount = len(excel_data.columns)
            for i in range(rowCount):
                employee = EmployeeModel()
                employee.Code = str(int(excel_data.iat[i, 0]))
                if isnull(excel_data.iat[i, 1]):
                    raise ProjectException(
                        f"Ô H{i + 4 + 1} bị trống, chưa có Họ & tên đệm.")
                employee.LastName = excel_data.iat[i, 1]
                if isnull(excel_data.iat[i, 2]):
                    raise ProjectException(
                        f"Ô H{i + 4 + 1} bị trống, chưa có tên")
                employee.FirstName = excel_data.iat[i, 2]
                if isnull(excel_data.iat[i, 3]):
                    raise ProjectException(
                        f"Ô H{i + 4 + 1} bị trống, chưa có ngày sinh.")
                employee.DateOfBirth = excel_data.iat[i, 3]
                if isnull(excel_data.iat[i, 3]):
                    raise ProjectException(
                        f"Ô H{i + 4 + 1} bị trống, chưa có giới tính.")
                employee.Gender = excel_data.iat[i, 4] == 1
                employee.Address = excel_data.iat[i, 5]
                employee.JoinDate = excel_data.iat[i, 6]
                if isnull(excel_data.iat[i, 7]):
                    raise ProjectException(
                        f"Ô H{i + 4 + 1} bị trống, chưa có email.")
                employee.Email = excel_data.iat[i, 7]
                employee.MobilePhone = str(excel_data.iat[i, 8])
                employee.Position = excel_data.iat[i, 9]
                employee.DepartmentId = int(excel_data.iat[i, 10])
                employee.CreatedAt = datetime.now()
                employee.ModifiedAt = datetime.now()
                employee.CreatedBy = id
                employee.ModifiedBy = id
                if EmployeeModel.query.filter_by(Email=employee.Email).first():
                    continue
                db.session.add(employee)
        elif fileExtension == 'csv':
            csv_data = pandas.read_csv(fileRequest, header=0)
            raise ProjectException(f"Không hỗ trợ file có phần mở rộng .{fileExtension}")
        app.logger.info("Importing EmployeeModel successful")
        db.session.commit()
        return {
            "Status": 1,
            "Description": None,
            "ResponseData": None
        }, 200

    except ProjectException as ex:
        db.session.rollback()
        app.logger.info(
            f"Importing EmployeeModel thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"{ex}",
            "ResponseData": None,
        }, 200

    except Exception as ex:
        db.session.rollback()
        app.logger.info(
            f"Importing EmployeeModel thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("Importing EmployeeModel kết thúc")

excelTemplatePath = path.join("..", "public", "templates", "Excel")

# GET api/employee/import/templates
@Employee.route("import/templates", methods=["GET", "POST"])
@admin_required()
def GetTemplate():
    try:
        app.logger.info("GetTemplate EmployeeModel bắt đầu")
        claims = get_jwt()
        id = claims['id']
        return send_from_directory(excelTemplatePath, "Employee.xlsx", as_attachment=True)
    except ProjectException as ex:
        db.session.rollback()
        app.logger.info(
            f"Importing EmployeeModel thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"{ex}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        db.session.rollback()
        app.logger.info(
            f"GetTemplate EmployeeModel thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("GetTemplate EmployeeModel kết thúc")

def CheckIfFileAllowed(filename):
    if ('.' not in filename):
        return False
    extension = GetFileExtensionFromFileNam(filename)
    if extension not in ALLOWED_EXTENSIONS:
        return False
    return True

def GetFileExtensionFromFileNam(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else None

@Employee.route("/search", methods=["POST"])
# @admin_required()
def SearchEmployees():
    try:
        app.logger.info(f"SearchEmployees bắt đầu")
        jsonRequestData = request.get_json()
        department = jsonRequestData["Department"] if "Department" in jsonRequestData else None
        result = EmployeeModel.GetEmployeeListByDepartment(department)
        return {
            "Status": 1,
            "Description": f"",
            "ResponseData": employeeInfoListSchema.dump(result),
        }, 200
    except ProjectException as ex:
        app.logger.error(
            f"SearchEmployees thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"{ex}",
            "ResponseData": None,
        }, 200
    except Exception as ex:
        app.logger.error(
            f"SearchEmployees thất bại. Có exception[{str(ex)}]")
        return {
            "Status": 0,
            "Description": f"Xảy ra lỗi ở máy chủ.",
            "ResponseData": None,
        }, 200
    finally:
        app.logger.info("SearchEmployees kết thúc")
