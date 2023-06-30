from datetime import datetime
from enum import Enum

from flask import current_app as app
from marshmallow import fields
from sqlalchemy import (ARRAY, Boolean, Column, Date, DateTime, Integer,
                        Numeric, String, Time, and_, delete, func, insert, or_)

from src import marshmallow
from src.db import db
from src.department.model import DepartmentModel, DepartmentSchema
from src.employee.model import EmployeeModel, EmployeeSchema
from src.shift.ShiftModel import ShiftModel
from src.utils.extension import ProjectException

# MODELS


class ShiftAssignment(db.Model):
    __tablename__ = "ShiftAssignment"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True)
    ShiftId = Column(Integer(), nullable=False)
    ShiftDetailId = Column(Integer(),  nullable=False)
    StartDate = Column(Date(),  nullable=False)
    EndDate = Column(Date())
    TargetType = Column(Integer(), nullable=True)
    Description = Column(String(), default='')
    Note = Column(String(), default='')
    Status = Column(String(), default='1')
    CreatedBy = Column(Integer())
    ModifiedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())
    DaysInWeek = Column(ARRAY(Integer()), nullable=False, default=[])

    def QueryDetails(self):
        try:
            employeeList = []
            departmentList = []
            total = 0
            if (self.TargetType == TargetType.Employee.value):
                query = db.select(EmployeeModel.Id, EmployeeModel.FirstName, EmployeeModel.LastName, EmployeeModel.Position, EmployeeModel.DepartmentId).where(and_(
                    ShiftAssignmentDetail.ShiftAssignmentId == self.Id, EmployeeModel.Id == ShiftAssignmentDetail.Target))
                # query = db.select(EmployeeModel.Id, EmployeeModel.FirstName, EmployeeModel.LastName, EmployeeModel.Position).where(and_(
                #     ShiftAssignmentEmployee.ShiftAssignmentId == self.Id, EmployeeModel.Id == ShiftAssignmentEmployee.EmployeeId))
                employeeList = EmployeeSchema(many=True).dump(
                    db.session.execute(query).all())
            elif (self.TargetType == TargetType.Department.value):
                query = db.select(DepartmentModel).where(and_(
                    ShiftAssignmentDetail.ShiftAssignmentId == self.Id, DepartmentModel.Id == ShiftAssignmentDetail.Target))
                # ShiftAssignmentDepartment.ShiftAssignmentId == self.Id, DepartmentModel.Id == ShiftAssignmentDepartment.DepartmentId))
                departmentList = DepartmentSchema(many=True).dump(
                    db.session.execute(query).scalars().all())

            return {
                "EmployeeList": employeeList,
                "DepartmentList": departmentList,
                "Total": len(employeeList) + len(departmentList)
            }
        except Exception as ex:
            app.logger.exception(
                f"ShiftAssignment.QueryDetails thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignment.QueryDetails thất bại. Có exception[{str(ex)}]")

    @staticmethod
    def QueryMany(Page: int = None, PerPage: int = None, SearchString: str = "", condition: str = ''):
        try:
            query = db.select(ShiftAssignment)
            if SearchString and SearchString.strip():
                sqlString = "%" + SearchString.strip().upper() + "%"
                query = query.where(or_(func.cast(ShiftAssignment.Id, String).like(
                    sqlString), func.upper(ShiftAssignment.Description).like(sqlString)))
            if condition and condition != "":
                query = query.where(condition)
            query = query.order_by(ShiftAssignment.Id)
            if not Page and not PerPage:
                data = db.session.execute(query).all()
                return {
                    "Items": data,
                    "Total": len(data)
                }
            data = db.paginate(query, page=Page, per_page=PerPage)
            return {
                "Items": data.items,
                "Total": data.total
            }
        except Exception as ex:
            app.logger.exception(
                f"ShiftAssignment.QueryMany thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignment.QueryMany thất bại. Có exception[{str(ex)}]")

    def InsertManyTargets(self, IdList: list, userId: int, target_type: int = None) -> bool:
        try:
            #     assignment_type = self.TargetType
            #     if assignment_type == TargetType.Department.value:
            #         insertArr = list(map(lambda x: {
            #             "DepartmentId": x,
            #             "ShiftAssignmentId": self.Id,
            #             "CreatedBy": userId,
            #             "ModifiedBy": userId,
            #         }, IdList))
            #         result = db.session.execute(
            #             insert(ShiftAssignmentDepartment), insertArr)

            #     elif assignment_type == TargetType.Employee.value:
            #         insertArr = list(map(lambda x: {
            #             "EmployeeId": x,
            #             "ShiftAssignmentId": self.Id,
            #             "CreatedBy": userId,
            #             "ModifiedBy": userId,
            #         }, IdList))
            #         result = db.session.execute(
            #             insert(ShiftAssignmentEmployee), insertArr)
            if len(IdList):
                insertArray = []
                for id in IdList:
                    insertArray.append({
                        "Target": id,
                        "ShiftAssignmentId": self.Id,
                        "CreatedBy": userId,
                        "ModifiedBy": userId,
                    })
                result = db.session.execute(
                    insert(ShiftAssignmentDetail), insertArray)
                print(result)
                db.session.commit()
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"ShiftAssignment.InsertManyTargets thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignment.InsertManyTargets thất bại. Có exception[{str(ex)}]")

    def RemoveBulkByTargets(self, TargetList: [], target_type: int = None) -> bool:
        try:
            assignment_type = self.TargetType if target_type is None else target_type
            if len(TargetList):
                query = delete(ShiftAssignmentDetail).where(and_(ShiftAssignmentDetail.ShiftAssignmentId == self.Id,
                                                                 ShiftAssignmentDetail.Target.in_(TargetList))
                                                            )
                db.session.execute(query)
                db.session.commit()
                # if assignment_type == TargetType.Department.value:
                #     query = delete(ShiftAssignmentDepartment).where(and_(
                #         ShiftAssignmentDepartment.ShiftAssignmentId == self.Id, ShiftAssignmentDepartment.DepartmentId.in_(TargetList)))
                #     db.session.execute(query)
                #     db.session.commit()
                # elif assignment_type == TargetType.Employee.value:
                #     query = delete(ShiftAssignmentEmployee).where(and_(
                #         ShiftAssignmentEmployee.ShiftAssignmentId == self.Id, ShiftAssignmentEmployee.EmployeeId.in_(TargetList)))
                #     db.session.execute(query)
                #     db.session.commit()
                # if query:
            return True
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"ShiftAssignmentDetail.RemoveBulkByIds thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignmentDetail.RemoveBulkByIds thất bại. Có exception[{str(ex)}]")


class ShiftAssignmentSchema(marshmallow.Schema):
    Id = fields.Integer()
    ShiftId = fields.Integer()
    ShiftDetailId = fields.Integer()
    StartDate = fields.Date()
    EndDate = fields.Date()
    TargetType = fields.Integer()
    Description = fields.String()
    Note = fields.String()
    Status = fields.Integer()
    CreatedBy = fields.Integer()
    CreatedAt = fields.DateTime()
    DaysInWeek = fields.List(fields.Integer())
    ShiftName = fields.Method("get_shift_name")
    EmployeeList = fields.Method("get_employee_list")
    DepartmentList = fields.Method("get_department_list")

    def get_shift_name(self, obj):
        try:
            if obj.ShiftId:
                result = ShiftModel.query.filter_by(Id=obj.ShiftId).first()
                if result:
                    return result.Description
            return ""
        except Exception as ex:
            app.logger.exception(
                f"ShiftAssignmentSchema.get_shift_name() failed. Exception: {ex}")
            return ""

    def get_employee_list(self, obj):
        try:
            if obj.TargetType != TargetType.Employee.value:
                return []
            employeeList = db.session.execute(
                db.select(vShiftAssignmentDetail.EmployeeName)
                .where(and_(vShiftAssignmentDetail.Id == obj.Id, vShiftAssignmentDetail.TargetType == TargetType.Employee.value)).limit(5)
            ).scalars().all()

            return employeeList
        except Exception as ex:
            app.logger.exception(
                f"ShiftAssignmentSchema.get_employee_list() failed. Exception: {ex}")
            return []

    def get_department_list(self, obj):
        try:
            if obj.TargetType != TargetType.Department.value:
                return []
            departmentList = db.session.execute(
                db.select(vShiftAssignmentDetail.DepartmentName)
                .where(and_(vShiftAssignmentDetail.Id == obj.Id, vShiftAssignmentDetail.TargetType == TargetType.Department.value)).limit(5)
            ).scalars().all()
            return departmentList
        except Exception as ex:
            app.logger.exception(
                f"ShiftAssignmentSchema.get_department_list() failed. Exception: {ex}")
            return []


class ShiftAssignmentDetail(db.Model):
    __tablename__ = "ShiftAssignmentDetail"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), autoincrement=True)
    ShiftAssignmentId = Column(Integer(), nullable=False,  primary_key=True)
    Target = Column(Integer(), nullable=False,  primary_key=True)
    Status = Column(String(), default='1')
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())

    @staticmethod
    def RemoveBulkByIds(IdList: []):
        try:
            if len(IdList):
                query = delete(ShiftAssignmentDetail).where(
                    ShiftAssignmentDetail.Id.in_(IdList))
                result = db.session.execute(query)
                print(result)
            return True
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"ShiftAssignmentDetail.RemoveBulkByIds thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignmentDetail.RemoveBulkByIds thất bại. Có exception[{str(ex)}]")

    @staticmethod
    def InsertBulk(values: list) -> list:
        try:
            result = db.session.execute(insert(ShiftAssignmentDetail), values)
            db.session.flush()
            print(result)
            return values
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"ShiftAssignmentDetail.InsertBulk thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignmentDetail.InsertBulk thất bại. Có exception[{str(ex)}]")

    @staticmethod
    def DisableBulk(IdList: list, userId: int = None) -> list:
        try:
            query = select(ShiftAssignmentDetail).where(
                ShiftAssignmentDetail.Id.in_(IdList))
            items = db.session.execute(query).scalars().all()
            for item in items:
                item.Status = '0'
                item.ModifiedAt = datetime.now()
                item.ModifiedBy = userId
            return values
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"ShiftAssignmentDetail.DisableBulk thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignmentDetail.DisableBulk thất bại. Có exception[{str(ex)}]")


class vShiftAssignmentDetail(db.Model):
    __tablename__ = "vShiftAssignmentDetail"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True)
    ShiftId = Column(Integer())
    ShiftDetailId = Column(Integer())
    StartDate = Column(Date())
    EndDate = Column(Date())
    TargetType = Column(Integer(), nullable=True)
    Target = Column(Integer(), nullable=True)
    Description = Column(String())
    Note = Column(String(), default='')
    Status = Column(String(), default='1')
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())
    DaysInWeek = Column(ARRAY(Integer()))
    EmployeeName = Column(String())
    DepartmentName = Column(String())
    DepartmentId = Column(Integer())
    EmployeeId = Column(Integer())
    StartTime = Column(Time())
    FinishTime = Column(Time())
    BreakAt = Column(Time())
    BreakEnd = Column(Time())
    HasBreak = Column(Boolean())
    WorkingHour = Column(Numeric(precision=10, scale=2))
    WorkingDay = Column(Numeric(precision=10, scale=2))


class ShiftAssignmentEmployee(db.Model):
    __tablename__ = "ShiftAssignment_Employee"
    __table_args__ = {'extend_existing': True}

    ShiftAssignmentId = Column(Integer(), primary_key=True)
    EmployeeId = Column(Integer(), primary_key=True)
    Status = Column(Integer(), default=1)
    CreatedAt = Column(DateTime(), default=datetime.now())
    CreatedBy = Column(Integer(), default=0)
    ModifiedAt = Column(DateTime(), default=datetime.now())
    ModifiedBy = Column(Integer(), default=0)

    def __init__(self):
        super().__init__()

    def __init__(self, shift_assignment_id: int, employee_id: int):
        try:
            if not ShiftAssignment.query.filter_by(Id=shift_assignment_id):
                raise ProjectException(
                    f"Không tìm thấy bảng phân ca {shift_assignment_id}")
            if not EmployeeModel.query.filter_by(Id=employee_id):
                raise ProjectException(
                    f"Không tìm thấy nhân viên {employee_id}")
            self.ShiftAssignmentId = shift_assignment_id
            self.EmployeeId = employee_id
        except ProjectException as pEx:
            app.logger.exception(
                f"ShiftAssignmentEmployee.__init__() Exception {pEx}")
            raise pEx
        except Exception as ex:
            app.logger.exception(
                f"ShiftAssignmentEmployee.__init__() Exception {ex}")
            raise ex


class ShiftAssignmentDepartment(db.Model):
    __tablename__ = "ShiftAssignment_Department"
    __table_args__ = {'extend_existing': True}

    ShiftAssignmentId = Column(Integer(), primary_key=True)
    DepartmentId = Column(Integer(), primary_key=True)
    Status = Column(Integer(), default=1)
    CreatedAt = Column(DateTime(), default=datetime.now())
    CreatedBy = Column(Integer(), default=0)
    ModifiedAt = Column(DateTime(), default=datetime.now())
    ModifiedBy = Column(Integer(), default=0)

    def __init__(self):
        super().__init__()

    def __init__(self, shift_assignment_id: int, department_id: int):
        try:
            if not ShiftAssignment.query.filter_by(Id=shift_assignment_id):
                raise ProjectException(
                    f"Không tìm thấy bảng phân ca {shift_assignment_id}")
            if not DepartmentModel.query.filter_by(Id=department_id):
                raise ProjectException(
                    f"Không tìm thấy phòng ban/ bộ phận {department_id}")
            self.ShiftAssignmentId = shift_assignment_id
            self.DepartmentId = department_id
        except ProjectException as pEx:
            app.logger.exception(
                f"ShiftAssignmentDepartment.__init__() Exception {pEx}")
            raise pEx
        except Exception as ex:
            app.logger.exception(
                f"ShiftAssignmentDepartment.__init__() Exception {ex}")
            raise ex


class ShiftAssignmentDetailSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftAssignmentId",
            "ShiftId",
            "ShiftDetailId"
            "DepartmentName",
            "DepartmentId",
            "EmployeeId",
            "EmployeeName",
            "StartDate",
            "EndDate",
            "TargetType",
            "DaysInWeek",
            "Description",
            "Status",
            "CreatedBy",
            "CreatedAt",
        )


class ShiftAssignmentType(db.Model):
    __tablename__ = "ShiftAssignmentType"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True)
    Name = Column(String(), unique=True)
    Name2 = Column(String())
    Status = Column(String())
    CreatedBy = Column(Integer())
    ModifiedBy = Column(Integer())
    CreatedAt = Column(DateTime())
    ModifiedAt = Column(DateTime())


class Status:
    Active = "1"
    Inactive = "2"


class TargetType(Enum):
    Employee = 1
    Department = 2


class DayInWeekEnum(Enum):
    Sun = 0,
    Mon = 1,
    Tue = 2,
    Wed = 3,
    Thur = 4,
    Fri = 5,
    Sat = 6
