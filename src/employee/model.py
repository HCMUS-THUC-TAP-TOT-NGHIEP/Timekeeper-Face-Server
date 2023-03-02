from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean
from datetime import datetime

# MODELS

class EmployeeModel(db.Model):
    __tablename__ = 'EmployeeInfo'

    Id = Column(Integer(), primary_key=True)
    FirstName = Column(String(), nullable=False)
    LastName = Column(String(), nullable=False)
    DateOfBirth = Column(DateTime(), nullable=False)
    Gender = Column(Boolean(), nullable=False)
    Address = Column(String(), nullable=False)
    JoinDate = Column(DateTime(), nullable=False)
    LeaveDate = Column(DateTime())
    DepartmentId = Column(Integer())
    CreatedBy = Column(Integer(), nullable=False)
    CreatedAt = Column(DateTime(), nullable=False)
    ModifiedBy = Column(Integer(), nullable=False)
    ModifiedAt = Column(DateTime(), nullable=False)

class EmployeeInfoSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "FirstName", "LastName", "DateOfBirth", "Gender", "Address", "JoinDate", "LeaveDate", "DepartmentId")

employeeInfoSchema = EmployeeInfoSchema()
employeeInfoListSchema = EmployeeInfoSchema(many=True)