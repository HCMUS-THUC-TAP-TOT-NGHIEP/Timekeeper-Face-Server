from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean
from datetime import datetime

class RecognitionData(db.Model):
    __tablename__ = "RecognitionData"
    Id = Column(Integer(), primary_key=True)
    EmployeeId = Column(Integer(), nullable=False)
    Key = Column(Integer())
    Url = Column(String())
    AccessUrl = Column(String())
    DownloadUrl = Column(String())
    CreatedAt = Column(DateTime())
    CreatedBy = Column(Integer())