# Copyright 2022 iiPython

# Modules
from webtransfer import app
from flask import render_template

# Routes
@app.route("/user/dashboard", methods = ["GET"])
def route_user_dash() -> None:
    return render_template("user/dashboard.html"), 200

@app.route("/user/friends", methods = ["GET"])
def route_user_friends() -> None:
    return render_template("user/friends.html"), 200
