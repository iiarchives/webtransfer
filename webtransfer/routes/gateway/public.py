# Copyright 2022 iiPython

# Modules
from webtransfer import app
from flask import render_template

# Routes
@app.route("/user/dashboard", methods = ["GET"])
def route_user_dash() -> None:
    return render_template("user/dashboard.html"), 200
