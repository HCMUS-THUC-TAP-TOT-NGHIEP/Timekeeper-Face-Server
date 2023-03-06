from flask import has_request_context, request, Flask, jsonify
import json
from flask_mail import Mail
from src.config import Config
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from src.db import db
from src.jwt import jwt
from logging.config import dictConfig
import logging
from logging.handlers import RotatingFileHandler
from flask_cors import CORS, cross_origin
from threading import Thread
from flask_marshmallow import Marshmallow

mail = Mail()
migrate = Migrate()
bcrypt = Bcrypt()
cors = CORS()
marshmallow = Marshmallow()
logger = logging.getLogger()


# create a formatter object
class LogFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.url = request.url
            record.remote_addr = request.remote_addr
        else:
            record.url = None
            record.remote_addr = None
        return super().format(record)


logFormatter = LogFormatter(
    "[%(asctime)s] %(remote_addr)s requested %(url)s\n"
    "%(levelname)s in %(module)s: %(message)s \n"
    "---------------------------------------------------------------\n\n"
)
# add file handler to the root logger
fileHandler = RotatingFileHandler("log.log", backupCount=100, maxBytes=1024 * 1024, encoding = "UTF-8")
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)


# init application
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    marshmallow.init_app(app)

    @app.before_request
    def log_request_info():
        args = request.args.to_dict()
        bodyData = request.get_data()
        if not bodyData:
            data = {}
        else:
            data = json.dumps(json.loads(bodyData), indent=2)
        Thread(
            app.logger.info(
                "\nHeaders: %s\nParams: %s\nRequestData: %s",
                request.headers,
                args,
                data,
            )
        ).start()

    @app.after_request
    def after_request(response):
        # response.status_code = 200
        Thread(
            app.logger.info(
                "\nHeaders: %s\nResponseData: %s", response.headers, response.data
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

    # endregion

    return app
