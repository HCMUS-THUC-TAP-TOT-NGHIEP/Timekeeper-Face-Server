from flask import request, Flask
import json
from src.config import Config
from flask_migrate import Migrate
from src.db import db
from src.jwt import jwt, get_jwt
from src.email import mail
from flask_cors import CORS
from threading import Thread
from flask_marshmallow import Marshmallow
from src.logger import logger, fileHandler

migrate = Migrate()
cors = CORS()
marshmallow = Marshmallow()


# init application
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    marshmallow.init_app(app)

    app.static_folder = "public"

    log_type = app.config["LOG_TYPE"]
    if log_type == "stream":
        pass
    else:
        logger.addHandler(fileHandler)

    app.logger.info("Connect to Database successfully!")

    @app.before_request
    def log_request_info():
        args = request.args.to_dict()
        bodyData = request.get_data()
        try:
            if not bodyData:
                data = {}
            else:
                data = (
                    json.dumps(json.loads(bodyData), indent=2)
                    .encode("utf-8")
                    .decode("utf-8")
                )
        except Exception as ex:
            data = str(bodyData)
        finally:
            Thread(
                app.logger.info(
                    "\nHeaders: %s\nParams: %s\nRequest Body: %s",
                    request.headers,
                    args,
                    data,
                )
            ).start()

    @app.after_request
    def after_request(response):
        try:
            exp_timestamp = get_jwt()["exp"]
            now = datetime.now()
            target_timestamp = datetime.timestamp(now + timedelta(minutes=10))
            app.logger.info(f"Check if refresh token {now}")
            if target_timestamp > exp_timestamp:
                access_token = create_access_token(identity=get_jwt_identity(), additional_claims=get_jwt())
                set_access_cookies(response, access_token)
                app.logger.info(f"Refresh token successfully {now}")
        except (RuntimeError, KeyError):
            # Case where there is not a valid JWT. Just return the original response
            pass
            # return response
        finally: 
            try:
                text_response = response.data
                if response.data:
                    text_response = (
                        json.dumps(json.loads(response.data), indent=4)
                        .encode("utf-8")
                        .decode("utf-8")
                    )
            except Exception as e:
                text_response = str(response).encode("utf-8").decode("utf-8")
            finally:
                Thread(
                    app.logger.info(
                        "\nHeaders: %s\nResponse Body: %s",
                        response.headers,
                        text_response,
                    )
                ).start()
                return response

    app.app_context().push()

    # region Đăng ký blueprints/ routes

    from src.authentication.routes import Authentication as auth_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    from src.user.routes import User as user_bp

    app.register_blueprint(user_bp, url_prefix="/api/user")

    from src.employee.routes import Employee as employee_bp

    app.register_blueprint(employee_bp, url_prefix="/api/employee")

    from src.department.routes import Department as department_bp

    app.register_blueprint(department_bp, url_prefix="/api/department")

    from src.shift.routes import Shift as shift_bp

    app.register_blueprint(shift_bp, url_prefix="/api/shift")
    from src.designation.routes import Designation as designation_bp

    app.register_blueprint(designation_bp, url_prefix="/api/designation")
    from src.employee_checkin.routes import EmployeeCheckinRoute as employee_checkin_bp

    app.register_blueprint(employee_checkin_bp, url_prefix="/api/checkin")
    from src.face_api.routes import FaceApi as face_api_bp

    app.register_blueprint(face_api_bp, url_prefix="/api/face")

    from src.attendance_machine.routes import AttendanceMachineApi as attendance_machine_api_bp

    app.register_blueprint(attendance_machine_api_bp, url_prefix="/api/attendance_machine/")

    @app.route("/")
    def index():
        return {
            "Status": 0,
            "Description": f"Welcome to Timekeeper-Face-Server",
            "ResponseData": None,
        }

    @app.errorhandler(404)
    def error404Handle(error):
        app.logger.error(f"Không hỗ trợ [{request}]. [{error}]")
        return {
            "Status": 0,
            "Description": f"Không hỗ trợ {request}",
            "ResponseData": None,
        }, 200

    @app.errorhandler(405)
    def error405Handle(error):
        return {
            "Status": 0,
            "Description": f"Không hỗ trợ {request}",
            "ResponseData": None,
        }, 200
    @app.errorhandler(401) #UNAUTHORIZED
    def error401Handle(error):
        app.logger.error(f"UNAUTHORIZED: [{error}]")
        return {
            "Status": 401,
            "Description": f"Phiên làm việc đã hết hạn, vui lòng đăng nhập lại",
            "ResponseData": None,
        }, 200

    # endregion

    return app
