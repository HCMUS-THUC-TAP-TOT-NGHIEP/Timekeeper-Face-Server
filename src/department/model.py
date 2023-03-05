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


class DepartmentSchema(marshmallow.Schema):
    class Meta:
        fields = (
            "Id",
            "Name",
            "Status",
        )

departmentSchema = DepartmentSchema()
departmentListSchema = DepartmentSchema(many=True)
