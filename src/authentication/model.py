from src.db import db
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from datetime import datetime
from src import marshmallow
# MODELS

class UserModel(db.Model):
    __tablename__ = 'User'
    
    Id = Column(Integer(), primary_key=True)
    EmailAddress = Column(String(), unique=True, nullable=False)
    PasswordHash = Column(String(), nullable=False)
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

class UserSchema(marshmallow.Schema):
    class Meta:
        fields=("Id", "EmailAddress", "UserName", "EmployeeId", "Status", "Role")

user_schema = UserSchema()
userList_schema = UserSchema(many=True)