from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, DateTime, Time, ARRAY, Boolean, Numeric
from enum import Enum
from datetime import datetime

# MODELS


# class ShiftModel(db.Model):
#     __tablename__ = "Shift"

#     Id = Column(Integer(), primary_key=True)
#     Description = Column(String(), nullable=False)
#     ShiftType = Column(Integer())
#     Status = Column(Integer(), default=1)
#     CreatedBy = Column(Integer())
#     CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
#     ModifiedBy = Column(Integer())
#     ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())

#     def __init__(self) -> None:
#         super().__init__()


# class ShiftDetailModel(db.Model):
#     __tablename__ = "ShiftDetail"
#     Id = Column(Integer(), primary_key=True)
#     ShiftId = Column(Integer(), nullable=False)
#     StartTime = Column(Time())
#     FinishTime = Column(Time())
#     BreakAt = Column(Time())
#     BreakEnd = Column(Time())
#     Note = Column(String(), default='')
#     BreakMinutes = Column(Integer(), default=0)
#     Status = Column(Integer(), default=1)
#     CreatedBy = Column(Integer())
#     CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
#     ModifiedBy = Column(Integer())
#     ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())
#     CheckinRequired = Column(Boolean(), default=True)
#     CheckoutRequired = Column(Boolean(), default=True)
#     HasBreak = Column(Boolean(), default=False)
#     WorkingHour = Column(Numeric(precision=5, scale=2))
#     WorkingDay = Column(Numeric(precision=5, scale=2))


# class ShiftDetailSchema(marshmallow.Schema):
#     class Meta:
#         fields = (
#             "Id",
#             "ShiftId",
#             "StartTime",
#             "FinishTime",
#             "BreakAt",
#             "BreakEnd",
#             "DayIndexList",
#             "BreakMinutes",
#             "Status",
#             "CheckinRequired",
#             "CheckoutRequired",
#             "HasBreak",
#             "WorkingHour",
#             "WorkingDay",
#         )


# class ShiftTypeModel(db.Model):
#     __tablename__ = "ShiftType"

#     Id = Column(Integer(), primary_key=True)
#     Description = Column(String())
#     Status = Column(Integer(), default=1)
#     CreatedBy = Column(Integer())
#     CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
#     ModifiedBy = Column(Integer())
#     ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())

#     def __init__(self) -> None:
#         super().__init__()


# class ShiftSchema(marshmallow.Schema):
#     class Meta:
#         fields = (
#             "Id",
#             "Description",
#             "StartTime",
#             "FinishTime",
#             "BreakAt",
#             "BreakEnd",
#             "Status",
#             "StatusText",
#             "StartDate",
#             "EndDate",
#             "CreatedAt",
#             "CreatedBy",
#             "ShiftType",
#             "ShiftTypeText",
#             "DayIndexList",
#             "Note",
#             "BreakMinutes"
#         )


# class ShiftListResponseSchema(marshmallow.Schema):
#     class Meta:
#         fields = (
#             "Id",
#             "Description",
#             "StartTime",
#             "FinishTime",
#             "BreakAt",
#             "BreakEnd",
#             "Status",
#             "StatusText",
#             "StartDate",
#             "EndDate",
#             "DayIndexList",
#             "Note",
#         )


# class ShiftTypeModelSchema(marshmallow.Schema):
#     class Meta:
#         fields = ("Id", "Description")


class ShiftAssignment(db.Model):
    __tablename__ = "ShiftAssignment"

    Id = Column(Integer(), primary_key=True)
    ShiftId = Column(Integer())
    ShiftDetailId = Column(Integer())
    # StartDate = Column(DateTime())
    # EndDate = Column(DateTime(), nullable=True)
    # AssignType = Column(Integer(), nullable=True)
    Description = Column(String())
    Note = Column(String(), default='')
    Status = Column(String(), default='1')
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())


class ShiftAssignmentSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftId",
            "Description",
            "Note",
            "Status",
            "CreatedBy",
            "CreatedAt",
        )


class ShiftAssignmentDetail(db.Model):
    __tablename__ = "ShiftAssignmentDetail"

    Id = Column(Integer(), primary_key=True)
    ShiftAssignmentId = Column(Integer())
    Target = Column(Integer())
    TargetType = Column(Integer())
    # FinishAssignmentTime = Column(Time())
    Status = Column(String(), default='1')
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())
    StartDate = Column(DateTime())
    EndDate = Column(DateTime(), nullable=True)
    ShiftId = Column(Integer())
    ShiftDetailId = Column(Integer())
    DaysInWeek = Column(ARRAY(Integer()))


class ShiftAssignmentDetailSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftAssignmentId",
            "Target",
            "TargetType",
            "Note",
            "Status",
            "CreatedBy",
            "CreatedAt",
            "EndDate",
            "StartDate",
            "ShiftId",
            "ShiftDetailId",
            "DaysInWeek",
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


# shiftSchema = ShiftSchema()
# shiftListSchema = ShiftSchema(many=True)
# shiftListResponseSchema = ShiftListResponseSchema(many=True)

Status = Enum("Status", ["Active", "Inactive"])
TargetType = Enum("TargetType", ["Department", "Employee"])


class Status:
    Active = "1"
    Inactive = "2"


class TargetType(Enum):
    Department = 1
    Employee = 2


class DayInWeekEnum(Enum):
    Sun = 0,
    Mon = 1,
    Tue = 2,
    Wed = 3,
    Thur = 4,
    Fri = 5,
    Sat = 6
