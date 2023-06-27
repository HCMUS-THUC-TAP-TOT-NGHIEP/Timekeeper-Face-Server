from datetime import *
from src.db import db
from src import marshmallow
from marshmallow import fields
from sqlalchemy import Column, Integer, String, SmallInteger, DateTime, Boolean
from flask import current_app as app


class RoleModel(db.Model):
    __tablename__ = 'Role'
    __table_args__ = {'extend_existing': True}
    Id = Column(Integer(), primary_key=True, autoincrement=True)
    Description = Column(String(255))
    Status = Column(String(255))
    CreatedAt = Column(DateTime(), default=datetime.now())
    ModifiedAt = Column(DateTime(), default=datetime.now())
    CreatedBy = Column(Integer())
    ModifiedBy = Column(Integer())
    extend_existing = True


class UserSchema(marshmallow.Schema):

    Id = fields.Integer()
    EmailAddress = fields.String()
    Username = fields.String()
    Name = fields.String()
    Status = fields.Integer()
    Role = fields.Integer()
    CreatedAt = fields.DateTime()
    CreatedBy = fields.Integer()
    ModifiedAt = fields.DateTime()
    ModifiedBy = fields.Integer()
    RoleText = fields.Method("get_role_text")

    def get_role_text(self, obj):
        try:
            if obj.Role and isinstance(obj.Role, int):
                result = RoleModel.query.filter_by(Id=obj.Role).first()
                if result is not None:
                    return result.Description
            return ""
        except Exception as ex:
            app.logger.exception(
                f"get_role_text of user {obj.Id} has exception[{ex}]")
            return ""


class RoleSchema(marshmallow.Schema):
    Id = fields.Integer()
    Description = fields.String()
    Status = fields.Integer()
