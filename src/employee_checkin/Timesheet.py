from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean, BigInteger, ARRAY, Date, Time, and_, between, func
from datetime import datetime, time, timedelta, date
from flask import current_app as app
from src.shift.model import vShiftAssignmentDetail, ShiftModel
from src.employee_checkin.AttendanceStatistic import AttendanceStatisticV2
from src.employee.model import EmployeeModel
from src.extension import ProjectException


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

    def InsertTimesheetDetail(self) -> None:
        try:
            #region query: ghi lại chi tiết chấm công
            app.logger.info(f"Timesheet.InsertTimesheetDetail start. ")

            if self.LockedStatus:
                raise ProjectException(f"Bảng chấm công mã {self.Id} - {self.Name} không thể chỉnh sửa vì đã khóa. ")
            DateFrom = self.DateFrom
            DateTo = self.DateTo
            DepartmentList = self.DepartmentList

            checkinRecordList = AttendanceStatisticV2.QueryMany(DateFrom=DateFrom, DateTo=DateTo)["items"]
            query = db.select(EmployeeModel)
            if len(DepartmentList) > 0:
                query = query.where(EmployeeModel.DepartmentId.in_(DepartmentList))
            employeeList = db.session.execute(query).scalars()
                
            # employeeList = employeeInfoListSchema.dump(data)
            db.session.execute(db.delete(TimesheetDetail).where(TimesheetDetail.TimesheetId == self.Id))
            delta = timedelta(days=1)     
            for employee in employeeList:
                # currentDate = date.fromisoformat(DateFrom)
                # endDate = date.fromisoformat(DateTo)
                currentDate = DateFrom
                endDate = DateTo
                while currentDate <= endDate:
                    timeSheetDetail = TimesheetDetail()
                    checkinRecords = list(filter(lambda x: x.Id == employee.Id and x.Date == currentDate, checkinRecordList))
                    counts = checkinRecords.__len__()
                    timeSheetDetail.EmployeeId = employee.Id
                    timeSheetDetail.Date = currentDate
                    timeSheetDetail.CheckinTime =  checkinRecords[0].Time if counts > 0 else None
                    timeSheetDetail.CheckoutTime = checkinRecords[1].Time if counts > 1 else None
                    timeSheetDetail.TimesheetId = self.Id
                    if timeSheetDetail.IncludeAssignment():
                        db.session.add(timeSheetDetail)
                    currentDate+=delta
            # endregion
            return
        except ProjectException as pEx:
            app.logger.exception(
                f"Timesheet.InsertTimesheetDetail failed. Exception[{pEx}]")
            raise pEx
        except Exception as ex:
            app.logger.exception(
                f"Timesheet.InsertTimesheetDetail failed. Exception[{ex}]")
            raise Exception(
                f"Timesheet.InsertTimesheetDetail failed. Exception[{ex}]")
        finally:
            app.logger.exception(f"Timesheet.InsertTimesheetDetail finish. ")

    def QueryDetails(self, EmployeeId=None, DepartmentId=None, Date=None):
            try:
                app.logger.info(f"Timesheet.QueryDetails start. ")
                query = db.select(vTimesheetDetail).where(vTimesheetDetail.TimesheetId == self.Id)
                data = db.session.execute(query).scalars().all()
                # return list(map(lambda x: x._asdict()["vTimesheetDetail"], data))
                return data
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
    LateMinutes = Column(Integer(), default=0)
    EarlyMinutes = Column(Integer(), default=0)

    def __init__(self) -> None:
        super().__init__()

    def IncludeAssignment(self) -> bool:
        try:
            app.logger.exception(f"TimesheetDetail.IncludeAssignment start. ")
            query = db.select(vShiftAssignmentDetail).where(and_(vShiftAssignmentDetail.EmployeeId == self.EmployeeId,
                                                                 between(self.Date, vShiftAssignmentDetail.StartDate, vShiftAssignmentDetail.EndDate)))
            result = db.session.execute(query).scalars().first()
            if result:
                self.ShiftAssignmentId = result.Id
                self.ShiftId = result.ShiftId
                self.BreakAt = result.BreakAt
                self.BreakEnd = result.BreakEnd
                self.StartTime = result.StartTime
                self.FinishTime = result.FinishTime
                if self.CheckinTime:
                    self.LateMinutes = self.CheckinTime.minute - self.StartTime.minute
                if self.CheckoutTime:
                    self.EarlyMinutes = self.FinishTime.minute - self.CheckoutTime.minute
                return True
            return False
        except Exception as ex:
            app.logger.exception(
                f"TimesheetDetail.IncludeAssignment failed. Exception[{ex}]")
            raise Exception(
                f"TimesheetDetail.IncludeAssignment failed. Exception[{ex}]")
        finally:
            app.logger.exception(f"TimesheetDetail.IncludeAssignment finish. ")

    

class vTimesheetDetail(db.Model):
    __tablename__ = "vTimesheetDetail"

    Id = Column(BigInteger(), primary_key=True)
    Date = Column(Date(), nullable=False)
    TimesheetId = Column(BigInteger(), nullable=False)
    EmployeeId = Column(Integer(), nullable=False)
    EmployeeName = Column(String())
    Department = Column(String())
    CheckinTime = Column(Time())
    CheckoutTime = Column(Time())
    ShiftAssignmentId = Column(Integer())
    ShiftId = Column(Integer())
    EmployeeCheckinId = Column(Integer())
    StartTime = Column(Time())
    FinishTime = Column(Time())
    BreakAt = Column(Time())
    BreakEnd = Column(Time())
    ShiftName = Column(String(), default="")

    def __init__(self) -> None:
        super().__init__()


class TimesheetDetailSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "TimesheetId", "EmployeeId", "Date", "CheckinTime", "CheckoutTime", "StartTime",
                  "FinishTime", "BreakAt", "BreakEnd", "ShiftAssignmentId", "ShiftId", "EmployeeCheckinId", "EmployeeName", "Department", "ShiftName")


timesheetSchema = TimesheetSchema()
timesheetListSchema = TimesheetSchema(many=True)
timesheetDetailSchema = TimesheetDetailSchema()
timesheetDetailListSchema = TimesheetDetailSchema(many=True)
