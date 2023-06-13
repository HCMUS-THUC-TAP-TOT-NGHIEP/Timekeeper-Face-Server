from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean
from datetime import datetime
from src.face_api.model import RecognitionData, RecognitionDataSchema
import base64
import uuid
from flask import current_app as app
# MODELS


class EmployeeCheckin(db.Model):
    __tablename__ = "EmployeeCheckin"
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
    def insert_one(app, employee_id, method, method_text, time: datetime, image_data):
        with app.app_context():
            try:
                new_obj = EmployeeCheckin(
                    employee_id, method, method_text, time, image_data)
                db.session.add(new_obj)
                db.session.commit()
            except Exception as ex:
                db.session.rollback()
                app.logger.exception(
                    f'EmployeeCheckin insertOne() has errors. Exception: {ex}')
                raise ex


class EmployeeCheckinSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "EmployeeId", "Method", "MethodText", "Time", "EvidenceId", "LogType",
                  "CreatedBy", "CreatedAt", "ModifiedBy", "ModifiedAt")


employeeCheckinSchema = EmployeeCheckinSchema()
employeeCheckinListSchema = EmployeeCheckinSchema(many=True)
