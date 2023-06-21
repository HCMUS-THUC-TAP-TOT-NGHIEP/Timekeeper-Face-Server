from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, DateTime, Time, ARRAY, Boolean, Numeric, Date, and_, insert, delete
from enum import Enum
from datetime import datetime
from flask import current_app as app
from src.employee.model import EmployeeModel, EmployeeSchema
from src.department.model import DepartmentModel, DepartmentSchema
from src.shift.ShiftModel import ShiftModel
from src.utils.extension import ProjectException

# MODELS


class ShiftAssignment(db.Model):
    __tablename__ = "ShiftAssignment"

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
                # query = db.select(EmployeeModel.Id, EmployeeModel.FirstName, EmployeeModel.LastName, EmployeeModel.Position).where(and_(
                #     ShiftAssignmentDetail.ShiftAssignmentId == self.Id, EmployeeModel.Id == ShiftAssignmentDetail.Target))
                query = db.select(EmployeeModel.Id, EmployeeModel.FirstName, EmployeeModel.LastName, EmployeeModel.Position).where(and_(
                    ShiftAssignmentEmployee.ShiftAssignmentId == self.Id, EmployeeModel.Id == ShiftAssignmentEmployee.EmployeeId))
                employeeList = EmployeeSchema(many=True).dump(
                    db.session.execute(query).all())
            elif (self.TargetType == TargetType.Department.value):
                query = db.select(DepartmentModel).where(and_(
                    # ShiftAssignmentDetail.ShiftAssignmentId == self.Id, DepartmentModel.Id == ShiftAssignmentDepartment.Target))
                    ShiftAssignmentDepartment.ShiftAssignmentId == self.Id, DepartmentModel.Id == ShiftAssignmentDepartment.DepartmentId))
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
    def QueryMany(Page: int = None, PerPage: int = None, condition: str = ''):
        try:
            query = db.select(ShiftAssignment.Id, ShiftAssignment.ShiftId, ShiftAssignment.ShiftDetailId, ShiftAssignment.StartDate, ShiftAssignment.EndDate,
                              ShiftAssignment.TargetType, ShiftAssignment.Description, ShiftAssignment.Note, ShiftAssignment.DaysInWeek, ShiftModel.Description.label("ShiftName"))
            if condition and condition != "":
                query = query.where(
                    and_(condition, ShiftAssignment.ShiftId == ShiftModel.Id))
            else:
                query = query.where(ShiftAssignment.ShiftId == ShiftModel.Id)

            if not Page and not PerPage:
                data = db.session.execute(query).all()
                return {
                    "Items": ShiftAssignmentSchema(many=True).dump(data),
                    "Total": len(data)
                }
            else:
                query = db.select(ShiftAssignment)
                if condition and condition != "":
                    query = query.where(condition)
                data = db.paginate(query, page=Page, per_page=PerPage)
                items = []
                for item in data.items:
                    shift = ShiftModel.query.filter_by(Id=item.ShiftId).first()
                    temp = ShiftAssignmentSchema().dump(item)
                    temp["ShiftName"] = shift.Description
                    items.append(temp)
                return {
                    "Items": items,
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
            assignment_type = self.TargetType
            if assignment_type == TargetType.Department.value:
                insertArr = list(map(lambda x: {
                    "DepartmentId": x,
                    "ShiftAssignmentId": self.Id,
                    "CreatedBy": userId,
                    "ModifiedBy": userId,
                }, IdList))
                result = db.session.execute(
                    insert(ShiftAssignmentDepartment), insertArr)

            elif assignment_type == TargetType.Employee.value:
                insertArr = list(map(lambda x: {
                    "EmployeeId": x,
                    "ShiftAssignmentId": self.Id,
                    "CreatedBy": userId,
                    "ModifiedBy": userId,
                }, IdList))
                result = db.session.execute(
                    insert(ShiftAssignmentEmployee), insertArr)
          # if len(IdList):
            #     insertArray = []
            #     for id in IdList:
            #         insertArray.append({
            #             "Target": id,
            #             "ShiftAssignmentId": self.Id,
            #             "CreatedBy": userId,
            #             "ModifiedBy": userId,
            #         })
            #     result = db.session.execute(
            #         insert(ShiftAssignmentDetail), insertArray)
            #     print(result)
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
                # query = delete(ShiftAssignmentDetail).where(and_(ShiftAssignmentDetail.ShiftAssignmentId == self.Id,
                #                                              ShiftAssignmentDetail.Target.in_(TargetList))
                #                                         )
                if assignment_type == TargetType.Department.value:
                    query = delete(ShiftAssignmentDepartment).where(and_(
                        ShiftAssignmentDepartment.ShiftAssignmentId == self.Id, ShiftAssignmentDepartment.DepartmentId.in_(TargetList)))
                elif assignment_type == TargetType.Employee.value:
                    query = delete(ShiftAssignmentEmployee).where(and_(
                        ShiftAssignmentEmployee.ShiftAssignmentId == self.Id, ShiftAssignmentEmployee.EmployeeId.in_(TargetList)))
                if query:
                    db.session.execute(query)
                    db.session.commit()
            return True
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"ShiftAssignmentDetail.RemoveBulkByIds thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignmentDetail.RemoveBulkByIds thất bại. Có exception[{str(ex)}]")


class ShiftAssignmentSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftId",
            "ShiftDetailId",
            "StartDate",
            "EndDate",
            "TargetType",
            "Description",
            "Note",
            "Status",
            "CreatedBy",
            "CreatedAt",
            "DaysInWeek",
            "ShiftName"
        )


class ShiftAssignmentDetail(db.Model):
    __tablename__ = "ShiftAssignmentDetail"

    Id = Column(Integer(), primary_key=True)
    ShiftAssignmentId = Column(Integer(), nullable=False,  primary_key=True)
    Target = Column(Integer(), nullable=False,  primary_key=True)
    Status = Column(String(), default='1')
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())

    @staticmethod
    def RemoveBulkByIds(IdList: []) -> bool:
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
