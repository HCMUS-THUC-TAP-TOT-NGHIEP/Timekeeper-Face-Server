import io
import pandas
import numpy as np
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.utils import secure_filename
import xlsxwriter
from src.utils.extension import ProjectException
from flask import current_app as app


def createTimesheetReport(data: list() = None) -> str:
    try:
        app.logger.exception(f"createReport start.")
        workbook = xlsxwriter.Workbook('Bảng chấm công')
        return ""
    except ProjectException as pEx:
        app.logger.exception(f"createReport exception[{pEx}]")
        raise pEx
    except Exception as ex:
        app.logger.exception(f"createReport exception[{pEx}]")
        raise ex
    finally:
        app.logger.exception(f"createReport finished.")
