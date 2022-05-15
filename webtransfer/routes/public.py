# Copyright 2022 iiPython

# Modules
from webtransfer import app, rpath
from flask import render_template, send_from_directory

# Routes
@app.route("/", methods = ["GET"])
def route_index() -> None:
    return render_template("public/index.html"), 200

@app.route("/nojs", methods = ["GET"])
def route_no_javascript() -> None:
    return render_template("public/nojs.html"), 200

@app.route("/s/<path:path>", methods = ["GET"])
def route_get_static_file(path: str) -> None:
    return send_from_directory(rpath("src/static"), path)
