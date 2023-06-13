from src.db import db
from src import marshmallow
from marshmallow import Schema, fields
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean, and_, select
from datetime import datetime
from flask import current_app as app
from src.department.model import DepartmentModel
# MODELS


class EmployeeModel(db.Model):
    __tablename__ = "EmployeeInfo"

    Id = Column(Integer(), primary_key=True)
    FirstName = Column(String(), nullable=False)
    LastName = Column(String(), nullable=False)
    DateOfBirth = Column(DateTime(), nullable=False)
    Gender = Column(Boolean(), nullable=False)
    Address = Column(String(), nullable=False)
    JoinDate = Column(DateTime(), nullable=False)
    LeaveDate = Column(DateTime())
    DepartmentId = Column(Integer())
    Position = Column(String())
    Email = Column(String())
    MobilePhone = Column(String())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime())

    def FullName(self):
        return " ".join([self.LastName, self.FirstName])

    @staticmethod
    def GetEmployeeListByDepartment(department: list[int] | int) -> list:
        try:
            app.logger.info(
                "EmployeeModel.GetEmployeeListByDepartment() bắt đầu")
            if isinstance(department, int) or isinstance(department, str):
                department_list = [department]
            else:
                department_list = department

            result = list()
            if None in department_list:
                data = db.session.execute(select(EmployeeModel).where(
                    EmployeeModel.DepartmentId == None)).scalars().all()
                if data:
                    result.extend(data)
            department_list.remove(None)
            if department_list and isinstance(department_list[0], int):
                data = db.session.execute(select(EmployeeModel).where(
                    EmployeeModel.DepartmentId.in_(department_list))).scalars().all()
                if data:
                    result.extend(data)
            return result
        except Exception as ex:
            app.logger.error(
                f"EmployeeModel.GetEmployeeListByDepartment() có exception[{str(ex)}]")
            raise ex
        finally:
            app.logger.info(
                "EmployeeModel.GetEmployeeListByDepartment() kết thúc")


class vEmployeeModel(db.Model):
    __tablename__ = "vEmployeeDetail"

    Id = Column(Integer(), primary_key=True)
    FirstName = Column(String(), nullable=False)
    LastName = Column(String(), nullable=False)
    DateOfBirth = Column(DateTime(), nullable=False)
    Gender = Column(Boolean(), nullable=False)
    Address = Column(String(), nullable=False)
    JoinDate = Column(DateTime(), nullable=False)
    LeaveDate = Column(DateTime())
    DepartmentId = Column(Integer())
    Position = Column(String())
    Email = Column(String())
    MobilePhone = Column(String())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime())
    DepartmentName = Column(String())

    def FullName(self):
        return " ".join([self.LastName, self.FirstName])


class EmployeeSchema(Schema):
    class Meta:
        fields = (
            "Id",
            "FirstName",
            "LastName",
            "DateOfBirth",
            "Gender",
            "Address",
            "JoinDate",
            "LeaveDate",
            "DepartmentId",
            "Position",
            "Email",
            "MobilePhone",
            "DepartmentName"
        )


employeeInfoSchema = EmployeeSchema()
employeeInfoListSchema = EmployeeSchema(many=True)
