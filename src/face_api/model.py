from src.db import db
from src import marshmallow
from marshmallow import fields
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean, BigInteger
from datetime import datetime
from src.services.DriveService import DriveService,  MimeType
from src.config import Config
import base64
import uuid
import os


class RecognitionData(db.Model):
    __tablename__ = "RecognitionData"
    Id = Column(BigInteger(), primary_key=True, autoincrement=True)
    EmployeeId = Column(Integer(), nullable=False)
    Key = Column(String())
    Url = Column(String())
    AccessUrl = Column(String())
    DownloadUrl = Column(String())
    CreatedAt = Column(DateTime(), default=datetime.now())
    CreatedBy = Column(Integer(), default=0)

    def __init__(self, employee_id, key, url, access_url, download_url, user_id):
        try:
            self.EmployeeId = employee_id
            self.Key = Key
            self.Url = url
            self.AccessUrl = access_url
            self.DownloadUrl = download_url
            db.session.add(self)
            db.session.flush()
            db.session.refresh(self)
            db.session.commit()
            return self.Id
        except Exception as ex:
            db.session.rollback()
            raise Exception(
                f'Không thể tạo object RecognitionData. Exception: {ex}')

    def __init__(self, employee_id, image_path, time: datetime, user_id: int = None, delete_after_save: bool = True):
        service = DriveService()
        try:
            self.EmployeeId = employee_id
            folder_name = time.__format__("%Y%m%d")
            folders = service.search_folder(
                query=f"(mimeType = '{MimeType.google_folder}') and (name = '{folder_name}') and ('{Config.DRIVE_FOLDER_ID}' in parents)")
            if folders is None or not folders:
                folder = service.create_folder(
                    folder_name=folder_name, parent_folder_id=Config.DRIVE_FOLDER_ID)
                if not folder:
                    return None
            else:
                folder = folders[0]
            file = service.upload_file(new_file_name=image_path,
                                       file_name=image_path, folder_id=folder["id"])
            if file is None:
                raise Exception(
                    "Không nhận được kết quả của lưu file lên google drive.")
            self.Key = file["id"]
            # self.Url = url
            self.AccessUrl = file["webViewLink"]
            self.DownloadUrl = file["webContentLink"]
            db.session.add(self)
            db.session.flush()
            db.session.refresh(self)
            db.session.commit()
        except Exception as ex:
            db.session.rollback()
            raise Exception(
                f'Không thể tạo object RecognitionData. Exception: {ex}')
        finally:
            if delete_after_save:
                os.remove(image_path)
                pass


class RecognitionDataSchema(marshmallow.SQLAlchemyAutoSchema):
    Id = fields.Integer()
    EmployeeId = fields.Integer()
    # EmployeeInfo = fields.Method("get_employee_name")
    Key = fields.String()
    Url = fields.String()
    AccessUrl = fields.String()
    DownloadUrl = fields.String()
    CreatedAt = fields.DateTime()
    CreatedBy = fields.Integer()
