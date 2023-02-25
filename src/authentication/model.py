from src.db import db
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from datetime import datetime
from marshmallow import Schema, fields, ValidationError, pre_load
from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field

# MODELS

class UserModel(db.Model):
    __tablename__ = 'User'
    
    Id = Column(Integer, primary_key=True)
    EmailAddress = Column(String(), unique=True, nullable=False)
    PasswordHash = Column(String(), nullable=False)
    PasswordSalt = Column(String())
    UserName = Column(String())
    EmployeeId = Column(Integer())
    Status = Column(SmallInteger())
    Role = Column(Integer())
    CreatedAt = Column(DateTime())
    CreatedBy = Column(Integer())
    ModifiedAt = Column(DateTime())
    ModifiedBy = Column(Integer())

    def __init__(self, email, password, salt, employee_id, status, role=None):
        self.EmailAddress = email
        self.PasswordHash = password
        self.PasswordSalt = salt
        self.EmployeeId = employee_id
        self.Status = status
        self.Role = role if role is not None else -1
        self.CreatedBy = 0
        self.CreatedAt = datetime.now()
        self.ModifiedBy = 0
        self.ModifiedAt = datetime.now()

#SCHEMA

class UserSchema(Schema):
    Id: fields.Int()
    EmailAddress: fields.Str()
    # UserName: fields.Str()
    # EmployeeId: fields.Str()
    # Status: fields.Int()
    # Role: fields.Int()
    # CreatedBy: fields.Int()
    # CreatedAt: fields.DateTime()
    # ModifiedBy: fields.Int()
    # ModifiedAt: fields.DateTime()

class UserSchema_(SQLAlchemySchema):
    class Meta:
        model = UserModel
        load_instance = True

    EmailAddress: auto_field()
    UserName: auto_field()
    EmployeeId: auto_field()