from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, DateTime, Time

# MODELS


class ShiftModel(db.Model):
    __tablename__ = "Shift"

    Id = Column(Integer(), primary_key=True)
    Description = Column(String(), nullable=False)
    StartTime = Column(Time(), nullable=False)
    FinishTime = Column(Time(), nullable=False)
    BreakAt = Column(Time(), nullable=False)
    BreakMinutes = Column(Integer(), nullable=False)
    BreakEnd = Column(Time(), nullable=False)
    Type = Column(Integer(), nullable=False)
    Status = Column(Integer())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(), nullable=False)
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(), nullable=False)

    def __init__(self) -> None:
        super().__init__()


class ShiftTypeModel(db.Model):
    __tablename__ = "ShiftType"

    Id = Column(Integer(), primary_key=True)
    Description = Column(String())
    CreatedBy = Column(Integer(), )
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
            "Type",
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
            "Type",
            "TypeText",
            "Status",
            "StatusText",
        )


class ShiftTypeModelSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "Description")


shiftSchema = ShiftSchema()
shiftListSchema = ShiftSchema(many=True)
shiftListResponseSchema = ShiftListResponseSchema(many=True)
