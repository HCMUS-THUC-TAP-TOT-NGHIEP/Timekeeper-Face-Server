from flask import Flask
from flask_mail import Mail
from src.config import Config

mail = Mail()

# Registering blueprints

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    mail.init_app(app)
    app.app_context().push()

    # Đăng ký blueprints/ routes
    from src.authentication.routes import Authentication as auth_bp
    from src.user.routes import User as user_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/user')

    return app