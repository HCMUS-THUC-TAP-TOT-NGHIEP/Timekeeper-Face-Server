from src.db import db
from src import marshmallow
from sqlalchemy import Column, Integer, String, DateTime

# MODELS


class DepartmentModel(db.Model):
    __tablename__ = "Department"

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
    Id = Column(Integer(), primary_key=True)
    Name = Column(String(), nullable=False)
    ManagerId = Column(Integer())
    ManagerName = Column(String())
    Status = Column(String(1), nullable=False)
    CreatedBy = Column(Integer(), nullable=False)
    CreatedAt = Column(DateTime(), nullable=False)
    ModifiedBy = Column(Integer(), nullable=False)
    ModifiedAt = Column(DateTime(), nullable=False)


class DepartmentSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "Name",
            "ManagerId",
            "ManagerName",
            "Status",
        )


departmentSchema = DepartmentSchema()
departmentListSchema = DepartmentSchema(many=True)
