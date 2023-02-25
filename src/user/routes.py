from flask import Blueprint, jsonify

User = Blueprint('user', __name__)

# POST api/user/create
@User.route('/create', methods=['POST'])
def create():
    return jsonify({"data": "create new user"})

# POST api/user/edit
@User.route('/edit', methods=['POST'])
def edit():
    return jsonify({"data": "edit user"})