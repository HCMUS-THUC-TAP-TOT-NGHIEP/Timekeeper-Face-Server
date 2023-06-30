from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, DateTime, Time, ARRAY, Boolean, Numeric, Date, delete, or_, func
from enum import Enum
from flask import current_app as app
from src.utils.extension import ProjectException
from datetime import datetime


class ShiftModel(db.Model):
    __tablename__ = "Shift"

    Id = Column(Integer(), primary_key=True)
    Description = Column(String(), nullable=False)
    ShiftType = Column(Integer())
    Status = Column(Integer(), default=1)
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())

    def __init__(self) -> None:
        super().__init__()

    @staticmethod
    def DeleteBulkByIds(IdList: list = [], userId: int = None) -> None:
        try:
            if len(IdList) > 0:
                query = delete(ShiftDetailModel).where(
                    ShiftDetailModel.ShiftId.in_(IdList))
                db.session.execute(query)
                query = delete(ShiftModel).where(ShiftModel.Id.in_(IdList))
                db.session.execute(query)
                db.session.commit()
                app.logger.info(
                    f"ShiftModel.DeleteBulkByIds đã xóa các {';'.join(map(str, IdList))}")
        except Exception as ex:
            db.session.rollback()
            raise Exception(f"ShiftModel.DeleteBulkByIds exception. {ex}")


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


class ShiftDetailModel(db.Model):
    __tablename__ = "ShiftDetail"
    Id = Column(Integer(), primary_key=True)
    ShiftId = Column(Integer(), nullable=False)
    StartTime = Column(Time())
    FinishTime = Column(Time())
    BreakAt = Column(Time())
    BreakEnd = Column(Time())
    Note = Column(String(), default='')
    CheckinRequired = Column(Boolean(), default=True)
    CheckoutRequired = Column(Boolean(), default=True)
    HasBreak = Column(Boolean(), default=False)
    WorkingHour = Column(Numeric(precision=10, scale=2))
    WorkingDay = Column(Numeric(precision=10, scale=2))
    Status = Column(Integer(), default=1)
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())


class ShiftDetailSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "ShiftId",
            "StartTime",
            "FinishTime",
            "BreakAt",
            "BreakEnd",
            "Status",
            "CheckinRequired",
            "CheckoutRequired",
            "HasBreak",
            "WorkingHour",
            "WorkingDay",
        )


class ShiftTypeModel(db.Model):
    __tablename__ = "ShiftType"

    Id = Column(Integer(), primary_key=True)
    Description = Column(String())
    Status = Column(Integer(), default=1)
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=None), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=None), default=datetime.now())

    def __init__(self) -> None:
        super().__init__()


class vShiftDetail(db.Model):
    __tablename__ = 'vShiftDetail'
    Id = Column(Integer(), primary_key=True)
    Description = Column(String())
    CreatedAt = Column(DateTime())
    Status = Column(Integer())
    StartTime = Column(Time(timezone=False))
    FinishTime = Column(Time(timezone=False))
    BreakAt = Column(Time(timezone=False))
    BreakEnd = Column(Time(timezone=False))
    HasBreak = Column(Boolean())
    WorkingDay = Column((Numeric(precision=10, scale=2)))
    WorkingHour = Column((Numeric(precision=10, scale=2)))
    DetailStatus = Column(Integer())
    CheckinRequired = Column(Boolean())
    CheckoutRequired = Column(Boolean())

    @staticmethod
    def QueryMany(Page=None, PageSize=None, SearchString: str = "", Condition=None) -> dict:
        try:
            app.logger.info(f"vShiftDetail.QueryMany bắt đầu")
            query = db.select(vShiftDetail)
            if SearchString and SearchString.strip():
                sqlString = "%" + SearchString.strip().upper() + "%"
                query = query.where(or_(func.cast(vShiftDetail.Id, String).like(
                    sqlString), func.upper(vShiftDetail.Description).like(sqlString)))
            query = query.order_by(vShiftDetail.Id)
            if PageSize and Page and PageSize > 0 and Page > 0:
                result = db.paginate(query, page=Page, per_page=PageSize)
                return {
                    "items": result.items,
                    "total": result.total
                }
            else:
                result = db.session.execute(query).scalars().all()
                return {
                    "items": result,
                    "total": len(result)
                }
        except Exception as ex:
            app.logger.exception(f"vShiftDetail có exception: {ex}")
            raise ProjectException(f"Truy vấn không thành công")


class vShiftDetailSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "Description",
            "CreatedAt",
            "Status",
            "StartTime",
            "FinishTime",
            "BreakAt",
            "BreakEnd",
            "HasBreak",
            "WorkingDay",
            "WorkingHour",
            "DetailStatus",
            "CheckinRequired",
            "CheckoutRequired",
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


shiftSchema = ShiftSchema()
shiftListSchema = ShiftSchema(many=True)
shiftListResponseSchema = ShiftListResponseSchema(many=True)
