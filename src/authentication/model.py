from src.db import db
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime
from datetime import datetime
from src import marshmallow
from werkzeug.security import generate_password_hash, check_password_hash

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

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, value):
        self.PasswordHash = generate_password_hash(value)

    def verify_password(self, password):
        return check_password_hash(self.PasswordHash, password)

    def __init__(self) -> None:
        super().__init__()

# SCHEMA


class UserSchema(marshmallow.Schema):
    class Meta:
        fields = ("Id", "EmailAddress", "Username",
                  "EmployeeId", "Status", "Role")


user_schema = UserSchema()
userList_schema = UserSchema(many=True)
