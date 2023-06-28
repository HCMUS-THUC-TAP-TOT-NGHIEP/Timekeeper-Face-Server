from flask import current_app as app
from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, Date, String, DateTime, and_, func, select, or_, asc
from datetime import datetime, date, timedelta
from src.employee.model import EmployeeModel
from src.department.model import DepartmentModel
from pandas import ExcelWriter, DataFrame
import os
import shutil
from src.utils.extension import ProjectException
from src.utils.helpers import daterange, DeleteFile, GetDayOfWeek
from threading import Thread
import threading
from openpyxl.styles import NamedStyle, Font

# MODELS


class AttendanceStatistic(db.Model):
    __tablename__ = "vAttendanceStatistic"
    __table_args__ = {'extend_existing': True}

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
            query = select(AttendanceStatistic)\
                .where(AttendanceStatistic.Date.between(DateFrom, DateTo))

            if Keyword and Keyword.strip() != "":
                Keyword = Keyword.strip().lower()
                query = query.where(func.lower(
                    AttendanceStatistic.EmployeeName).like(f'%{Keyword}%'))

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
            if Page and PageSize:
                data = db.paginate(query, page=Page, per_page=PageSize)
            else:
                data = db.session.execute(query).scalars().all()
            return data
        except Exception as ex:
            app.logger.exception(
                f"AttendanceStatistic.QueryManyV2 failed. Exception[{ex}]")
            raise Exception(
                f"AttendanceStatistic.QueryManyV2 failed. Exception[{ex}]")


class AttendanceStatisticSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "EmployeeName", "FirstCheckin", "LastCheckin", "Time",
                  "Date", "DepartmentId", "DepartmentName", "Position", "Method", "MethodText", "AccessUrl", "DownloadUrl")


class AttendanceStatisticV2(db.Model):
    __tablename__ = "vAttendanceStatisticV2"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True)
    EmployeeName = Column(String())
    DepartmentId = Column(Integer())
    DepartmentName = Column(String())
    Position = Column(String())
    Method = Column(Integer(), primary_key=True)
    MethodText = Column(String())
    Time = Column(DateTime(), primary_key=True)
    Date = Column(Date())
    AccessUrl = Column(String())
    DownloadUrl = Column(String())

    @staticmethod
    def QueryMany(DateFrom, DateTo, MethodList: list(), Keyword=None, Page=None, PageSize=None):
        try:
            app.logger.info(f"AttendanceStatisticV2.QueryMany start")
            query = ""
            query = select(AttendanceStatisticV2).where(
                AttendanceStatisticV2.Date.between(DateFrom, DateTo))
            if Keyword and Keyword.strip() != "":
                Keyword = Keyword.strip().lower()
                query = query.where(func.lower(
                    AttendanceStatisticV2.EmployeeName).like(f'%{Keyword}%'))

            if MethodList and len(MethodList):
                query = query.where(
                    AttendanceStatisticV2.Method.in_(MethodList))

            query = query.distinct().order_by(AttendanceStatisticV2.Date,
                                              AttendanceStatisticV2.Id, AttendanceStatisticV2.Time)
            if Page and PageSize:
                data = db.paginate(query, page=Page, per_page=PageSize)
                return data
            data = db.session.execute(query).all()
            return {"items": list(map(lambda x: x._asdict()["AttendanceStatisticV2"], data)), "count": len(data)}
        except Exception as ex:
            app.logger.exception(
                f"AttendanceStatisticV2.QueryMany failed. Exception[{ex}]")
            raise Exception(
                f"AttendanceStatisticV2.QueryMany failed. Exception[{ex}]")
        finally:
            app.logger.info(f"AttendanceStatisticV2.QueryMany finish")

    @staticmethod
    def ExportReport(DateFrom: date, DateTo: date, Keyword: str = None) -> str:
        path = ""
        try:
            app.logger.info(f"AttendanceStatisticV2.ExportReport() start.")
            templatePath = os.path.join(
                os.pardir, app.static_folder, "templates", "Excel", f'CheckinData.xlsx')
            path = os.path.join(os.pardir, app.static_folder, "export",
                                f'Dữ liệu chấm công_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx')
            shutil.copyfile(templatePath, path)
            writer = ExcelWriter(path, engine="openpyxl",
                                 mode="a", if_sheet_exists="overlay")

            data = []
            stt = 1

            departmentList = db.session.execute(
                db.select(DepartmentModel)).scalars().all()
            # for department in departmentList:
            employeeList = db.session.execute(
                db.select(EmployeeModel).order_by(asc(EmployeeModel.DepartmentId), asc(EmployeeModel.Id))).scalars().all()
            department = -1
            for employee in employeeList:
                prefixData = [employee.Id, " ".join(
                    [employee.LastName, employee.FirstName])]
                if employee.DepartmentId != department:
                    temp = list(
                        filter(lambda x: x.Id == employee.DepartmentId, departmentList))
                    if temp and len(temp) > 0:
                        prefixData.append(temp[0].Name)
                    else:
                        prefixData.append(None)
                for date in daterange(DateFrom, DateTo):
                    rec = [stt]
                    rec.extend(prefixData)
                    rec.extend(
                        [date.strftime("%d/%m/%Y"), GetDayOfWeek(date)])
                    checkinList = db.session.execute(db.select(AttendanceStatisticV2).where(and_(
                        AttendanceStatisticV2.Id == employee.Id, AttendanceStatisticV2.Date == date))).scalars().all()
                    if not checkinList or len(checkinList) == 0:
                        rec.extend([None, None, None, None])
                    else:
                        date = checkinList[0].Time.strftime("%d/%m/%Y")
                        time = checkinList[0].Time.strftime("%H:%M")
                        rec.append(date)
                        rec.append(time)
                        if len(checkinList) > 1:
                            date = checkinList[1].Time.strftime("%d/%m/%Y")
                            time = checkinList[1].Time.strftime("%H:%M")
                            rec.append(date)
                            rec.append(time)
                    data.append(rec)
                    stt += 1

            df = DataFrame(data=data)
            df.to_excel(writer,  sheet_name="Main", startcol=0, startrow=6,
                        float_format="%.2f", index=False, header=False, na_rep="-")
            dataStyle = NamedStyle(name="DataStyle")
            dataStyle.font = Font(size=8, name="Tahoma")
            worksheet = writer.sheets["Main"]
            for cells in worksheet.iter_rows(min_row=7):
                for cell in cells:
                    cell.style = dataStyle
            writer.close()
            return path
        except ProjectException as pEx:
            t = threading.Thread(target=DeleteFile, args=(
                path, datetime.now() + timedelta(seconds=3)))
            t.start()
            app.logger.exception(
                f"AttendanceStatisticV2.ExportReport failed. Exception[{pEx}]")
            raise pEx
        except Exception as ex:
            app.logger.exception(
                f"AttendanceStatisticV2.ExportReport failed. Exception[{ex}]")
            t = threading.Thread(target=DeleteFile, args=(
                path, datetime.now() + timedelta(seconds=3)))
            t.start()
            raise ex
        finally:
            app.logger.info(f"AttendanceStatisticV2.ExportReport() finish.")


attendanceStatisticSchema = AttendanceStatisticSchema()
