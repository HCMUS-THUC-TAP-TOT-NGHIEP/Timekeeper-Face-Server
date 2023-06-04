from datetime import date, datetime, time, timedelta
from src.utils.helpers import daterange, subtractTime
from flask import current_app as app, url_for
from sqlalchemy import (ARRAY, BigInteger, Boolean, Column, Date, DateTime,
                        Integer, Numeric, SmallInteger, String, Time, and_,
                        between, func, delete)

from src import marshmallow
from src.db import db
from src.employee.model import EmployeeModel, vEmployeeModel
from src.department.model import DepartmentModel
from src.employee_checkin.AttendanceStatistic import AttendanceStatisticV2
from src.extension import ProjectException
from src.shift.model import ShiftModel, vShiftAssignmentDetail
import io
import os
from pandas import ExcelWriter, DataFrame
import numpy as np
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename
from xlsxwriter import Workbook


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

    def __str__(self):
        return self.Name.replace('/', '-')

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

    @staticmethod
    def DeleteById(id: int = None) -> bool:
        try:
            if id is None:
                raise ProjectException(
                    "Yêu cầu không hợp lệ, do chưa cung cấp mã báo cáo.")
            timesheet = Timesheet.query.filter_by(Id=id).first()
            if not timesheet:
                raise ProjectException(
                    f"Yêu cầu không thành công, do không tìm thấy bảng chấm công mã {id}.")
            db.session.execute(delete(TimesheetDetail).where(
                TimesheetDetail.TimesheetId == id))
            db.session.delete(timesheet)
            db.session.commit()
            return True
        except ProjectException as pEx:
            db.session.rollback()
            app.logger.exception(
                f"Timesheet.DeleteById thất bại. Có exception[{str(pEx)}]")
            raise pEx
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f"Timesheet.DeleteById thất bại. Có exception[{str(ex)}]")
            raise Exception(
                f"Timesheet.DeleteById thất bại. Có exception[{str(ex)}]")
        finally:
            app.logger.info(f"Timesheet.DeleteById kết thúc")

    def InsertTimesheetDetail(self) -> None:
        try:
            # region query: ghi lại chi tiết chấm công
            app.logger.info(f"Timesheet.InsertTimesheetDetail start. ")
            if self.LockedStatus:
                raise ProjectException(
                    f"Bảng chấm công mã {self.Id} - {self.Name} không thể chỉnh sửa vì đã khóa. ")
            DateFrom = self.DateFrom
            DateTo = self.DateTo
            DepartmentList = self.DepartmentList
            checkinRecordList = AttendanceStatisticV2.QueryMany(
                DateFrom=DateFrom, DateTo=DateTo)["items"]
            query = db.select(EmployeeModel)
            if len(DepartmentList) > 0:
                query = query.where(
                    EmployeeModel.DepartmentId.in_(DepartmentList))
            employeeList = db.session.execute(query).scalars()
            db.session.execute(db.delete(TimesheetDetail).where(
                TimesheetDetail.TimesheetId == self.Id))
            delta = timedelta(days=1)
            for employee in employeeList:
                currentDate = DateFrom
                endDate = DateTo
                while currentDate <= endDate:
                    timeSheetDetail = TimesheetDetail()
                    checkinRecords = list(filter(
                        lambda x: x.Id == employee.Id and x.Date == currentDate, checkinRecordList))
                    counts = checkinRecords.__len__()
                    timeSheetDetail.EmployeeId = employee.Id
                    timeSheetDetail.Date = currentDate
                    timeSheetDetail.CheckinTime = checkinRecords[0].Time.time(
                    ) if counts > 0 else None
                    timeSheetDetail.CheckoutTime = checkinRecords[1].Time.time(
                    ) if counts > 1 else None
                    timeSheetDetail.TimesheetId = self.Id
                    if timeSheetDetail.IncludeAssignment():
                        db.session.add(timeSheetDetail)
                    currentDate += delta
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
            query = db.select(vTimesheetDetail).where(
                vTimesheetDetail.TimesheetId == self.Id)
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

    def CreateTimesheetReport(self) -> str:
        try:
            app.logger.info(f"Timesheet.CreateTimesheetReport() start.")
            detail_records = self.QueryDetails()
            path = os.path.join(os.pardir,
                                app.static_url_path, "export", f'{self.__str__()}_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx')

            writer = ExcelWriter(path, engine="xlsxwriter")

            startRow = 5
            startColumn = 1
            startIndex = 0
            columns = ["STT", "Mã nhân viên", "Tên nhân viên",
                       "Phòng ban", "Vị trí công việc"]
            columns.extend([date.day.__str__() for date in daterange(self.DateFrom, self.DateTo)])
            columns.extend(["Số lần ĐMVS", "Số phút ĐMVS", "KCC"])
            if self.DepartmentList:
                departmentList = DepartmentList
            else:
                departmentList = db.session.execute(
                    db.select(DepartmentModel.Id)).scalars().all()

            currentRow = startRow
            currentColumn = startColumn
            stt = 1
            data = []
            for department in departmentList:
                employeeList = vEmployeeModel.query.filter_by(
                    DepartmentId=department).all()
                for employee in employeeList:
                    row = [stt, employee.Id, employee.FullName(), employee.DepartmentName, employee.Position]
                    total_minute = 0
                    count_late_early = 0
                    count_no_timekeeping = 0
                    for date in daterange(self.DateFrom, self.DateTo):
                        query = db.select(vTimesheetDetail).where(and_(vTimesheetDetail.TimesheetId == self.Id, vTimesheetDetail.EmployeeId == employee.Id, vTimesheetDetail.Date == date))
                        record = db.session.execute(query).scalars().first()
                        if not record:
                            row.append( float("NAN"))
                            count_no_timekeeping += 1
                            continue
                        if not record.DaysInWeek:
                            row.append(float("NAN"))
                            continue
                        if date.isoweekday() not in record.DaysInWeek:
                            row.append("")
                            continue
                        if not record.CheckinTime:
                            row.append(float("NAN"))
                            count_no_timekeeping += 1
                            continue
                        if not record.CheckoutTime:
                            row.append(float("NAN"))
                            count_no_timekeeping += 1
                            continue
                        time0 = record.StartTime
                        if record.LateMinutes > 0:
                            total_minute += record.LateMinutes
                            count_late_early += 1
                            time0 = record.CheckinTime

                        time1 = record.FinishTime
                        if record.EarlyMinutes > 0:
                            total_minute += record.LateMinutes
                            count_late_early += 1
                            time1 = record.CheckoutTime
                        delta = subtractTime(time0, time1)
                        if record.BreakAt and record.BreakEnd:
                            if record.CheckinTime < record.BreakAt:
                                delta = delta - subtractTime(record.BreakAt, record.BreakEnd)
                            else:
                                delta = delta - subtractTime(record.BreakEnd, time1)

                        row.append(delta / (60*float(record.WorkingHour)) * (float(record.WorkingDay)))
                    row.append(count_late_early)
                    row.append(total_minute)
                    row.append(count_no_timekeeping)
                    data.append(row)
                    stt+=1

            df = DataFrame(data=data, columns=columns)
            df.to_excel(writer,  sheet_name="Main", startcol=0, startrow=4, float_format="%.2f", index=False, header=False, na_rep="#NA")
            workbook = writer.book
            worksheet = writer.sheets["Main"]
            worksheet.set_column(1, 1, 15)
            worksheet.set_column(2, 4, 30)
            length = columns.__len__()
            worksheet.set_column(length - 3, length - 1, 15)
            # Add a header format.
            header_format = workbook.add_format(
                {
                    "bold": True,
                    "fg_color": "#D7E4BC",
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    "font_name": "Tahoma",
                    "font_size": "10",
                }
            )
            title_format = workbook.add_format({
                    "bold": True,
                    "valign": "vcenter",
                    "font_name": "Tahoma",
                    "font_size": "16",

            })
            # Write the column headers with the defined format.
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(3, col_num, value, header_format)
            worksheet.write(1, 0, self.Name, title_format)
            return path
        except ProjectException as pEx:
            app.logger.exception(
                f"Timesheet.CreateTimesheetReport() exception[{pEx}]")
            raise pEx
        except Exception as ex:
            app.logger.exception(
                f"Timesheet.CreateTimesheetReport() exception[{ex}]")
            raise ex
        finally:
            writer.close()
            app.logger.info(f"Timesheet.CreateTimesheetReport() finished.")


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
            shiftAssignment = db.session.execute(query).scalars().first()
            if shiftAssignment:
                self.ShiftAssignmentId = shiftAssignment.Id
                self.ShiftId = shiftAssignment.ShiftId
                self.BreakAt = shiftAssignment.BreakAt
                self.BreakEnd = shiftAssignment.BreakEnd
                self.StartTime = shiftAssignment.StartTime
                self.FinishTime = shiftAssignment.FinishTime
                if self.CheckinTime:
                    hourDiff = self.CheckinTime.hour - shiftAssignment.StartTime.hour
                    minDiff = self.CheckinTime.minute - shiftAssignment.StartTime.minute
                    lateMinutes = hourDiff*60 + minDiff
                    self.LateMinutes = lateMinutes
                if self.CheckoutTime:
                    earlyMinutes = datetime.combine(date.today(
                    ), shiftAssignment.FinishTime) - datetime.combine(date.today(), self.CheckoutTime)
                    self.EarlyMinutes = earlyMinutes.total_seconds() / 60
            return True
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
    StartTime = Column(Time())
    FinishTime = Column(Time())
    BreakAt = Column(Time())
    BreakEnd = Column(Time())
    ShiftName = Column(String(), default="")
    LateMinutes = Column(Integer(), default=0)
    EarlyMinutes = Column(Integer(), default=0)
    DaysInWeek = Column(ARRAY(Integer()))
    WorkingHour = Column(Numeric(precision=10, scale=2))
    WorkingDay = Column(Numeric(precision=10, scale=2))

    def __init__(self) -> None:
        super().__init__()


class TimesheetDetailSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "TimesheetId", "EmployeeId", "Date", "CheckinTime", "CheckoutTime", "StartTime",
                  "FinishTime", "BreakAt", "BreakEnd", "ShiftAssignmentId", "ShiftId", "EmployeeName", "Department", "ShiftName", "LateMinutes", "EarlyMinutes")


timesheetSchema = TimesheetSchema()
timesheetListSchema = TimesheetSchema(many=True)
timesheetDetailSchema = TimesheetDetailSchema()
timesheetDetailListSchema = TimesheetDetailSchema(many=True)
