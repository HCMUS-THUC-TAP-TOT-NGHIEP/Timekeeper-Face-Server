from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean
from datetime import datetime

# MODELS


class EmployeeCheckin(db.Model):
    __tablename__ = "EmployeeCheckin"
    Id = Column(Integer(), primary_key=True)
    EmployeeId = Column(Integer(), nullable=False)
    Method = Column(Integer())
    MethodText = Column(String())
    Time = Column(DateTime(timezone=False))
    EvidenceId = Column(Integer())
    LogType = Column(Integer())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=False))
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=False))


class EmployeeCheckinSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "EmployeeId" ,"Method", "MethodText", "Time", "EvidenceId", "LogType",
                  "CreatedBy", "CreatedAt", "ModifiedBy", "ModifiedAt")

employeeCheckinSchema = EmployeeCheckinSchema()
employeeCheckinListSchema = EmployeeCheckinSchema(many=True)
