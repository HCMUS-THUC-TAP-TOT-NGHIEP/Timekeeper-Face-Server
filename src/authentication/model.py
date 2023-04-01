from src.db import db
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from datetime import datetime
from src import marshmallow

# MODELS


class UserModel(db.Model):
    __tablename__ = "User"

    Id = Column(Integer(), primary_key=True)
    EmailAddress = Column(String(), unique=True, nullable=False)
    PasswordHash = Column(String(), nullable=False)
    Username = Column(String())
    EmployeeId = Column(Integer())
    Status = Column(SmallInteger())
    Role = Column(Integer())
    CreatedAt = Column(DateTime())
    CreatedBy = Column(Integer())
    ModifiedAt = Column(DateTime())
    ModifiedBy = Column(Integer())
    Name = Column(String())
    def __init__(self) -> None:
        super().__init__()


# SCHEMA


class UserSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "EmailAddress", "Username", "EmployeeId", "Status", "Role")


user_schema = UserSchema()
userList_schema = UserSchema(many=True)
