# Copyright 2022 iiPython

# Modules
from webtransfer import app
from flask import request, session, redirect, url_for, render_template

# Handle auth
@app.before_request
def check_auth() -> None:
    ep = request.endpoint or "/"
    if "userauth" not in session and "route_user_" in ep:
        if ep.split("_")[-1] not in ["login", "register"]:
            return redirect(url_for("route_user_login"))

# Routes
@app.route("/user/login", methods = ["GET", "POST"])
def route_user_login() -> None:
    if "userauth" in session:
        return redirect(url_for("route_user_dash"))

    elif request.method == "GET":
        return render_template("user/auth/login.html"), 200

    # Check for fields
    try:
        username, password = request.form["username"], request.form["password"]
        for val in [username, password]:
            if type(val) != str or not val.strip():
                raise ValueError

    except (KeyError, ValueError):
        return render_template("user/auth/login.html", message = "Please fill out all fields."), 400

    # Perform a database check
    auth_data = app.db("auth").check_login(username, password)
    if auth_data is None:
        return render_template("user/auth/login.html", message = "Invalid username or password."), 403

    session["userauth"] = auth_data
    return redirect(url_for("route_user_dash"))

@app.route("/user/register", methods = ["GET", "POST"])
def route_user_register() -> None:
    if "userauth" in session:
        return redirect(url_for("route_user_dash"))

    elif request.method == "GET":
        return render_template("user/auth/register.html"), 200

    # Check for fields
    try:
        username, password = request.form["username"], request.form["password"]
        for val in [username, password]:
            if type(val) != str or not val.strip():
                raise ValueError

    except (KeyError, ValueError):
        return render_template("user/auth/register.html", error = "fill-all-fields"), 400

    # Perform a registration
    error = app.db("auth").register(username, password)
    if error:
        return render_template("user/auth/register.html", username = username, error = error), 400

    session["userauth"] = app.db("auth").check_login(username, password)
    return redirect(url_for("route_user_dash"))

@app.route("/user/logout", methods = ["GET"])
def route_user_logout() -> None:
    if "userauth" in session:
        del session["userauth"]

    return redirect(url_for("route_user_login"))
