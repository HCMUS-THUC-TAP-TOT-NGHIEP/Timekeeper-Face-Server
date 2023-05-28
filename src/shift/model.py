from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, DateTime, Time, ARRAY, Boolean, Numeric, Date, and_, insert, delete
from enum import Enum
from datetime import datetime
from flask import current_app as app
from src.employee.model import EmployeeModel, EmployeeSchema
from src.department.model import DepartmentModel, DepartmentSchema
from src.shift.ShiftModel import ShiftModel

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
                query = db.select(EmployeeModel.Id, EmployeeModel.FirstName, EmployeeModel.LastName, EmployeeModel.Position, vShiftAssignmentDetail.DepartmentName).where(and_(
                    vShiftAssignmentDetail.Id == self.Id, EmployeeModel.Id == vShiftAssignmentDetail.EmployeeId))
                employeeList = EmployeeSchema(many=True).dump(
                    db.session.execute(query).all())
            elif (self.TargetType == TargetType.Department.value):
                query = db.select(DepartmentModel).where(and_(
                    vShiftAssignmentDetail.Id == self.Id, DepartmentModel.Id == vShiftAssignmentDetail.DepartmentId))
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

    def InsertManyTargets(self, IdList: list, userId: int) -> bool:
        try:
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
            return True
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"ShiftAssignment.RemoveBulkByIds thất bại. Có exception[{str(ex)}]"
            )
            raise Exception(
                f"ShiftAssignment.RemoveBulkByIds thất bại. Có exception[{str(ex)}]")

    def RemoveBulkByTargets(self, TargetList: []) -> bool:
        try:
            if len(TargetList):
                query = delete(ShiftAssignmentDetail).where(and_(ShiftAssignmentDetail.ShiftAssignmentId == self.Id,
                                                                ShiftAssignmentDetail.Target.in_(TargetList))
                                                            )
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
    ShiftAssignmentId = Column(Integer(), nullable=False)
    Target = Column(Integer(), nullable=False)
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


class ShiftAssignmentDetailSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftAssignmentId",
            "ShiftId",
            "ShiftDetailId"
            "EmployeeName",
            "StartDate",
            "EndDate",
            "DepartmentName",
            "DepartmentId",
            "EmployeeId",
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
