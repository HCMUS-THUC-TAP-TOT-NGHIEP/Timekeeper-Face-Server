from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt_identity,
    verify_jwt_in_request
)

jwt = JWTManager()