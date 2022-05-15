# Copyright 2022 iiPython

# Modules
from webtransfer import app
from flask import request, jsonify

# Routes
@app.route("/user/api/uvalidate", methods = ["GET"])
def route_user_uvalidate() -> None:
    users = request.args.get("users", "").split(",")
    if not users:
        return jsonify(code = 400, message = "No users provided to validate."), 400

    return jsonify(code = 200, users = app.db("auth").check_users(users)), 200
