from marshmallow import fields
from sqlalchemy import Column, DateTime, Integer, String, func, text

from src import marshmallow
from src.db import db
from flask import current_app as app

# region MODELS


class DepartmentModel(db.Model):
    __tablename__ = "Department"
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True)
    Name = Column(String(), nullable=False)
    ManagerId = Column(Integer())
    Status = Column(String(1), nullable=False)
    CreatedBy = Column(Integer(), nullable=False)
    CreatedAt = Column(DateTime(), nullable=False)
    ModifiedBy = Column(Integer(), nullable=False)
    ModifiedAt = Column(DateTime(), nullable=False)

    def __init__(self) -> None:
        super().__init__()


class vDepartment(db.Model):
    __tablename__ = 'vDepartment'
    __table_args__ = {'extend_existing': True}

    Id = Column(Integer(), primary_key=True)
    Name = Column(String(), nullable=False)
    ManagerId = Column(Integer())
    ManagerName = Column(String())
    Status = Column(String(1), nullable=False)
    CreatedBy = Column(Integer(), nullable=False)
    CreatedAt = Column(DateTime(), nullable=False)
    ModifiedBy = Column(Integer(), nullable=False)
    ModifiedAt = Column(DateTime(), nullable=False)

    def __init__(self) -> None:
        super().__init__()


class DepartmentSchema(marshmallow.Schema):
    Id = fields.Integer()
    Name = fields.String()
    ManagerId = fields.Integer()
    ManagerName = fields.String()
    EmployeeTotal = fields.Method("get_total_of_employees")
    Status = fields.Integer()
    CreatedAt = fields.DateTime()
    ModifiedAt = fields.DateTime()

    def get_total_of_employees(self, obj):
        try:
            t = text(
                'SELECT * FROM "EmployeeInfo" WHERE "DepartmentId" = :department_id')
            result = db.session.execute(
                t, {"department_id": obj.Id}).scalars().all()
            return len(result)
        except Exception as ex:
            app.logger.exception(
                f"DepartmentSchema.get_total_of_employees() failed. Has exception {ex}")
            return 0

# endregion


departmentSchema = DepartmentSchema()
departmentListSchema = DepartmentSchema(many=True)
