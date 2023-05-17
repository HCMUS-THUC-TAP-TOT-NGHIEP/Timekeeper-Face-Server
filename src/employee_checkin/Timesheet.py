from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean, BigInteger, ARRAY, Date, Time
from datetime import datetime
from flask import current_app as app


class Timesheet(db.Model):
    __tablename__ = "Timesheet"
    Id = Column(BigInteger(), primary_key=True)
    Name = Column(String(), nullable=False)
    DateFrom = Column(Date(), nullable=False)
    DateTo = Column(Date(), nullable=False)
    DepartmentList = Column(ARRAY(Integer()), nullable=False)
    LockedStatus = Column(Boolean(), nullable=False, default=False)
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime())

    def __init__(self) -> None:
        super().__init__()

    def Lock(self):
        app.logger.info(f"Lock bảng công chi tiết mã {self.Id}")
        self.LockedStatus = True
        db.session.commit()

    @staticmethod
    def QueryMany(LockedStatus=None, Keyword=None, Page=None, PageSize=None):
        try:
            app.logger.info(f"Timesheet.QueryMany start. ")
            condition = ""
            if Keyword and Keyword.strip() != "":
                Keyword = Keyword.strip().lower()
                condition = func.lower(Timesheet.Name).like(f'%{Keyword}%')
            if LockedStatus:
                condition = and_(
                    condition, Timesheet.LockedStatus == LockedStatus)
            query = db.select(Timesheet)
            if condition:
                query = query.where(condition)
            if not Page:
                Page = 1
            if not PageSize:
                PageSize = 50
            data = db.paginate(query, page=Page, per_page=PageSize)
            return data
        except Exception as ex:
            app.logger.exception(
                f"Timesheet.QueryMany failed. Exception[{ex}]")
            raise Exception(
                f"Timesheet.QueryMany failed. Exception[{ex}]")
        finally:
            app.logger.exception(f"Timesheet.QueryMany finish. ")

    def QueryDetails(self, EmployeeId=None, DepartmentId=None, Date=None):
        try:
            app.logger.info(f"Timesheet.QueryDetails start. ")
            condition = TimesheetDetail.TimesheetId == self.Id
            query = db.select(TimesheetDetail)
            if condition:
                query = query.where(condition)
            data = db.session.execute(query).all()
            return list(map(lambda x: x._asdict()["TimesheetDetail"], data))
        except Exception as ex:
            app.logger.exception(
                f"Timesheet.QueryDetails failed. Exception[{ex}]")
            raise Exception(
                f"Timesheet.QueryDetails failed. Exception[{ex}]")
        finally:
            app.logger.exception(f"Timesheet.QueryDetails finish. ")


class TimesheetSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "Name", "DateFrom", "DateTo",
                  "DepartmentList", "LockedStatus")


class TimesheetDetail(db.Model):
    __tablename__ = "TimesheetDetail"

    Id = Column(BigInteger(), primary_key=True)
    TimesheetId = Column(BigInteger(), nullable=False)
    EmployeeId = Column(Integer(), nullable=False)
    Date = Column(Date(), nullable=False)
    CheckinTime = Column(Time())
    CheckoutTime = Column(Time())
    ShiftAssignmentId = Column(Integer())
    ShiftId = Column(Integer())
    EmployeeCheckinId = Column(Integer())
    StartTime = Column(Time())
    FinishTime = Column(Time())
    BreakAt = Column(Time())
    BreakEnd = Column(Time())

    def __init__(self) -> None:
        super().__init__()


class TimesheetDetailSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "TimesheetId", "EmployeeId", "Date", "CheckinTime", "CheckoutTime", "StartTime",
                  "FinishTime", "BreakAt", "BreakEnd", "ShiftAssignmentId", "ShiftId", "EmployeeCheckinId")


timesheetSchema = TimesheetSchema()
timesheetListSchema = TimesheetSchema(many=True)
timesheetDetailSchema = TimesheetDetailSchema()
timesheetDetailListSchema = TimesheetDetailSchema(many=True)
