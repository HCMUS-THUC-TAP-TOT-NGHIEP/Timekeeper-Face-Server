from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, DateTime, Time, ARRAY
from enum import Enum

# MODELS


class ShiftModel(db.Model):
    __tablename__ = "Shift"

    Id = Column(Integer(), primary_key=True)
    Description = Column(String(), nullable=False)
    ShiftType = Column(Integer(), nullable=False)
    Status = Column(Integer())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(), nullable=False)
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(), nullable=False)

    def __init__(self) -> None:
        super().__init__()


class ShiftDetailModel(db.Model):
    __tablename__ = "ShiftDetail"
    Id = Column(Integer(), primary_key=True)
    ShiftId = Column(Integer(), nullable=False)
    StartDate = Column(Time(), nullable=False)
    EndDate = Column(Time(), nullable=False)
    StartTime = Column(Time(), nullable=False)
    FinishTime = Column(Time(), nullable=False)
    BreakAt = Column(Time())
    BreakEnd = Column(Time())
    DayIndexList = Column(ARRAY(Integer))
    Note = Column(String())
    BreakMinutes = Column(Integer())
    Status = Column(Integer())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime())


class ShiftDetailSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftId",
            "StartDate",
            "EndDate",
            "StartTime",
            "FinishTime",
            "BreakAt",
            "BreakEnd",
            "DayIndexList",
            "BreakMinutes",
            "Status",
            "Note",
        )


class ShiftTypeModel(db.Model):
    __tablename__ = "ShiftType"

    Id = Column(Integer(), primary_key=True)
    Description = Column(String())
    Status = Column(Integer())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(), nullable=False)
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(), nullable=False)

    def __init__(self) -> None:
        super().__init__()


class ShiftSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "Description",
            "StartTime",
            "FinishTime",
            "BreakAt",
            "BreakEnd",
            "Status",
            "StatusText",
            "StartDate",
            "EndDate",
            "CreatedAt",
            "CreatedBy",
            "ShiftType",
            "ShiftTypeText",
            "DayIndexList",
            "Note",
            "BreakMinutes"
        )


class ShiftListResponseSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "Description",
            "StartTime",
            "FinishTime",
            "BreakAt",
            "BreakEnd",
            "Status",
            "StatusText",
            "StartDate",
            "EndDate",
            "DayIndexList",
            "Note",
        )


class ShiftTypeModelSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "Description")


class ShiftAssignment(db.Model):
    __tablename__ = "ShiftAssignment"

    Id = Column(Integer(), primary_key=True)
    ShiftId = Column(Integer(), nullable=False)
    ShiftDetailId = Column(Integer(), nullable=False)
    StartDate = Column(DateTime(), nullable=False)
    EndDate = Column(DateTime(), nullable=True)
    AssignType = Column(Integer(), nullable=True)
    Description = Column(String(), nullable=False)
    Note = Column(String())
    Status = Column(String())
    CreatedBy = Column(Integer())
    ModifiedBy = Column(Integer())
    CreatedAt = Column(DateTime())
    ModifiedAt = Column(DateTime())


class ShiftAssignmentSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftId",
            "Description",
            "StartDate",
            "EndDate",
            "AssignType",
            "ShiftDescription",
            "Note",
            "Status",
            "CreatedBy",
            "CreatedAt",
            "AssignmentTypeName",
        )


class ShiftAssignmentDetail(db.Model):
    __tablename__ = "ShiftAssignmentDetail"

    Id = Column(Integer(), primary_key=True)
    ShiftAssignmentId = Column(Integer(), nullable=False)
    Target = Column(Integer(), nullable=False)
    TargetType = Column(Integer(), nullable=False)
    FinishAssignmentTime = Column(Time())
    Status = Column(String())
    CreatedBy = Column(Integer())
    ModifiedBy = Column(Integer())
    CreatedAt = Column(DateTime())
    ModifiedAt = Column(DateTime())


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


shiftSchema = ShiftSchema()
shiftListSchema = ShiftSchema(many=True)
shiftListResponseSchema = ShiftListResponseSchema(many=True)

Status = Enum("Status", ["Active", "Inactive"])
TargetType = Enum("TargetType", ["Department", "Designation", "Employee"])


class Status:
    Active = "1"
    Inactive = "2"


class TargetType(Enum):
    Department = 1
    Employee = 2
