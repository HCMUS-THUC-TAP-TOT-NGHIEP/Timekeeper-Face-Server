from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean


class Designation(db.Model):
    __tablename__ = "Designation"

    Id = Column(Integer(), primary_key=True)
    Name = Column(String(), nullable=False)
    Description = Column(String(), nullable=False)
    Status = Column(String(1))
    CreatedAt = Column(DateTime())
    ModifiedAt = Column(DateTime())
    CreatedBy = Column(Integer())
    ModifiedBy = Column(Integer())


class DesignationSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "Name", "Description", "Status")


designationSchema = DesignationSchema()
designationListSchema = DesignationSchema(many=True)
