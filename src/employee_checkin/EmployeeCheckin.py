from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean
from datetime import datetime
from src.face_api.model import RecognitionData, RecognitionDataSchema
import base64
import uuid
from flask import current_app as app
from marshmallow import fields
import random

# MODELS


class EmployeeCheckin(db.Model):
    __tablename__ = "EmployeeCheckin"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True, autoincrement=True)
    EmployeeId = Column(Integer(), nullable=False)
    Method = Column(Integer())
    MethodText = Column(String())
    Time = Column(DateTime(timezone=False))
    EvidenceId = Column(Integer())
    LogType = Column(Integer())
    CreatedBy = Column(Integer())
    CreatedAt = Column(DateTime(timezone=False), default=datetime.now())
    ModifiedBy = Column(Integer())
    ModifiedAt = Column(DateTime(timezone=False), default=datetime.now())

    def __init__(self, employee_id, method, method_text, time: datetime, image_data):
        try:
            # decode base64 string data
            decoded_data = base64.b64decode((image_data))
            # write the decoded data back to original format in  file
            image_path = uuid.uuid4().__str__() + ".png"
            img_file = open(image_path, 'wb')
            img_file.write(decoded_data)
            img_file.close()

            recognitionData = RecognitionData(
                employee_id=employee_id, image_path=image_path, time=time)
            db.session.add(recognitionData)
            db.session.flush()
            db.session.refresh(recognitionData)

            self.Method = method
            self.MethodText = method_text
            self.EmployeeId = employee_id
            self.Time = time
            self.EvidenceId = recognitionData.Id
            self.LogType = 0
        except Exception as ex:
            db.session.rollback()
            app.logger.exception(
                f'EmployeeCheckin constructor has errors. Exception: {ex}')
            raise ex

    @staticmethod
    def InsertOne(app, employee_id, method, method_text, time, image_data):
        with app.app_context():
            try:
                new_obj = EmployeeCheckin(
                    employee_id, method, method_text, time, image_data)
                db.session.add(new_obj)
                db.session.commit()
                return new_obj
            except Exception as ex:
                db.session.rollback()
                app.logger.exception(
                    f'EmployeeCheckin insertOne() has errors. Exception: {ex}')
                raise ex

    @staticmethod
    def CountLateEarly(date: datetime) -> int:
        try:
            app.logger.info(f"EmployeeCheckin.CountLateEarly() start")
            count = random.randint(0, 7)
            return count
        except Exception as ex:
            app.logger.exception(
                f'EmployeeCheckin CountLateEarly() has errors. Exception: {ex}')
            return 0

    @staticmethod
    def CountOff(date: datetime) -> int:
        try:
            app.logger.info(f"EmployeeCheckin.CountLateEarly() start")
            count = random.randint(0, 7)
            return count
        except Exception as ex:
            app.logger.exception(
                f'EmployeeCheckin CountLateEarly() has errors. Exception: {ex}')
            return 0


class EmployeeCheckinSchema(marshmallow.Schema):
    Id = fields.Integer()
    EmployeeId = fields.Integer()
    Method = fields.Integer()
    MethodText = fields.Method("GetCheckinMethod")
    Time = fields.DateTime()
    EvidenceId = fields.Integer()
    CreatedBy = fields.Integer()
    ModifiedBy = fields.Integer()
    CreatedAt = fields.DateTime()
    ModifiedAt = fields.DateTime()

    def GetCheckinMethod(self, obj):
        try:
            if obj.Method:
                result = CheckinMethodModel.query.filter_by(
                    Id=obj.Method).first()
                if result:
                    return result.Description
            return ""
        except Exception as ex:
            app.logger.exception(
                f"GetCheckinMethod of {obj.Method} has exception[{ex}] ")
            return ""


class CheckinMethodModel(db.Model):
    __tablename__ = "CheckinMethod"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True, autoincrement=True)
    Description = Column(String(), nullable=False, unique=True)
    Status = Column(Integer(), nullable=False, default=1)
    CreatedAt = Column(DateTime(), nullable=False, default=datetime.now())
    ModifiedAt = Column(DateTime(), nullable=False, default=datetime.now())
    CreatedBy = Column(Integer(), nullable=False)
    ModifiedBy = Column(Integer(), nullable=False)


class CheckinMethodSchema(marshmallow.Schema):
    Id = fields.Integer()
    Description = fields.String()
    Status = fields.Integer()
    CreatedAt = fields.DateTime()
    ModifiedAt = fields.DateTime()
    CreatedBy = fields.Integer()
    ModifiedBy = fields.Integer()


employeeCheckinSchema = EmployeeCheckinSchema()
employeeCheckinListSchema = EmployeeCheckinSchema(many=True)
