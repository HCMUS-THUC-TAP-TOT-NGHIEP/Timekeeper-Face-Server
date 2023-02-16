from flask import Blueprint, jsonify

Authentication = Blueprint('auth', __name__, url_prefix="/api/auth")

# GET api/auth/register
@Authentication.route('/register')
def register():
    return jsonify({"data": "register"})