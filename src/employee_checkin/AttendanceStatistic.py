from flask import current_app as app
from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, Date, String, DateTime, and_, func, select
from datetime import datetime
from src.employee.model import EmployeeModel

# MODELS


class AttendanceStatistic(db.Model):
    __tablename__ = "vAttendanceStatistic"
    Id = Column(Integer(), primary_key=True)
    EmployeeName = Column(String(), nullable=False)
    FirstCheckin = Column(DateTime(timezone=False))
    LastCheckin = Column(DateTime(timezone=False))
    Date = Column(Date(), primary_key=True)
    Position = Column(String())
    DepartmentId = Column(Integer())
    DepartmentName = Column(String())

    @staticmethod
    def QueryMany(DateFrom, DateTo, Keyword=None):
        try:
            query = ""
            if Keyword and Keyword.strip() != "":
                Keyword = Keyword.strip().lower()
                query = select(AttendanceStatistic)\
                    .where(and_(AttendanceStatistic.Date.between(DateFrom, DateTo),
                                func.lower(AttendanceStatistic.EmployeeName).like(f'%{Keyword}%')))
            else:
                query = select(AttendanceStatistic)\
                    .where(AttendanceStatistic.Date.between(DateFrom, DateTo))
            data = db.session.execute(query).scalars()
            return data
        except Exception as ex:
            app.logger.exception(
                f"AttendanceStatistic.QueryMany failed. Exception[{ex}]")
            raise Exception(
                f"AttendanceStatistic.QueryMany failed. Exception[{ex}]")

    @staticmethod
    def QueryManyV2(DateFrom, DateTo, Keyword=None, Page=None, PageSize=None):
        try:
            query = ""
            if Keyword and Keyword.strip() != "":
                Keyword = Keyword.strip().lower()
                query = select(AttendanceStatistic)\
                    .where(and_(AttendanceStatistic.Date.between(DateFrom, DateTo),
                                func.lower(AttendanceStatistic.EmployeeName).like(f'%{Keyword}%')))
            else:
                query = select(AttendanceStatistic)\
                    .where(AttendanceStatistic.Date.between(DateFrom, DateTo))
            if not Page:
                Page = 1
            if not PageSize:
                PageSize = 50
            data = db.paginate(query, page=Page, per_page=PageSize)
            return data
        except Exception as ex:
            app.logger.exception(
                f"AttendanceStatistic.QueryManyV2 failed. Exception[{ex}]")
            raise Exception(
                f"AttendanceStatistic.QueryManyV2 failed. Exception[{ex}]")


class AttendanceStatisticSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "EmployeeName", "FirstCheckin", "LastCheckin",
                  "Date", "DepartmentId", "DepartmentName", "Position")


attendanceStatisticSchema = AttendanceStatisticSchema()