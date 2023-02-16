from flask import Blueprint, jsonify

Authentication = Blueprint('auth', __name__, url_prefix="/auth")

# GET api/auth/register
Authentication.route('/register', method= ["GET"])
def register():
    return jsonify({"data": "register"})