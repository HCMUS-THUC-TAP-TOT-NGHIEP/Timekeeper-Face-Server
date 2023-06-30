from datetime import datetime

from flask import current_app as app
from marshmallow import Schema, fields
from sqlalchemy import (Boolean, Column, DateTime, Integer, SmallInteger,
                        String, and_, func, or_)

from src import marshmallow
from src.db import db
from src.department.model import DepartmentModel

# MODELS


class EmployeeModel(db.Model):
    __tablename__ = "EmployeeInfo"
    __table_args__ = {'extend_existing': True} 

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
                    EmployeeModel.DepartmentId == None).order_by(EmployeeModel.Id)).scalars().all()
                if data:
                    result.extend(data)
            department_list.remove(None)
            if department_list and isinstance(department_list[0], int):
                data = db.session.execute(select(EmployeeModel).where(
                    EmployeeModel.DepartmentId.in_(department_list)).order_by(EmployeeModel.Id)).scalars().all()
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

    @staticmethod
    def GetEmployeeList(department: list[int], name: str, page: int=0, perPage: int=0):
        '''
        Tìm kiếm nhân viên
        Trả về danh sách nhân viên
        Args:
        department: phòng ban hoặc danh sách phòng ban
        name: họ hoặc tên
        page: trang
        perPage: số nhân viên trên 1 trang
        '''
        try:
            query = db.select(EmployeeModel)
            if department:
                if None in department:
                # query = query.where(EmployeeModel.DepartmentId.in_(department))
                    query = query.where(or_(EmployeeModel.DepartmentId.in_(department), EmployeeModel.DepartmentId == None))
                else:
                    query = query.where(EmployeeModel.DepartmentId.in_(department))
            if name and name.strip():
                query = query.where(func.concat(func.upper(EmployeeModel.LastName)," ", func.upper(EmployeeModel.FirstName)).like(f"%{name.upper()}%"))
            query = query.order_by(EmployeeModel.DepartmentId, EmployeeModel.Id)
            if page and perPage:
                result = db.paginate(query, page=page, per_page=perPage)
                return {
                    "EmployeeList": employeeInfoListSchema.dump(result.items),
                    "Total": result.total
                }
            else:
                result = db.session.execute(query).scalars().all()
                return {
                    "EmployeeList": employeeInfoListSchema.dump(result),
                    "Total": len(result)
                }
        except Exception as ex:
            app.logger.error(
                f"EmployeeModel.GetEmployeeList() có exception[{str(ex)}]")
            raise ex
        finally:
            app.logger.info(
                "EmployeeModel.GetEmployeeList() kết thúc")



class vEmployeeModel(db.Model):
    __tablename__ = "vEmployeeDetail"
    __table_args__ = {'extend_existing': True} 

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


class EmployeeSchema(marshmallow.SQLAlchemyAutoSchema):
    Id = fields.Integer()
    FirstName = fields.String()
    LastName = fields.String()
    DateOfBirth = fields.Date()
    Gender = fields.Boolean()
    Address = fields.String()
    JoinDate = fields.Date()
    LeaveDate = fields.Date()
    DepartmentId = fields.Integer()
    Position = fields.String()
    Email = fields.String()
    MobilePhone = fields.String()
    # DepartmentName = fields.String()
    DepartmentName = fields.Method("get_department_name")
    FullName = fields.Method("get_full_name")

    def get_full_name(self, object):
        return " ".join([object.LastName, object.FirstName])

    def get_department_name(self, object):
        try:
            if object.DepartmentName:
                return object.DepartmentName
        except:
            try:
                department = DepartmentModel.query.filter_by(
                    Id=object.DepartmentId).first()
                if department:
                    return department.Name
                return ""
            except Exception as ex:
                # print(ex)
                return ""


employeeInfoSchema = EmployeeSchema()
employeeInfoListSchema = EmployeeSchema(many=True)
