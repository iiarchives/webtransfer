# Copyright 2022 iiPython

# Modules
import os
from webtransfer import app, rpath
from werkzeug.utils import secure_filename
from flask import request, session, jsonify, send_file

# Initialization
upload_directory = os.path.abspath(rpath("../db/uploads"))
if not os.path.isdir(upload_directory):
    os.makedirs(upload_directory)

upload_limit = 6 * (1024 ** 3)

def scale_bytes(bytecount: int) -> str:
    for unit in ["", "K", "M", "G"]:
        if abs(bytecount) < 1024:
            return f"{bytecount:3.1f}{unit}B"

        bytecount /= 1024

    return f"{bytecount:.1f}GB"

def calculate_usage(userhash: str) -> int:
    user_directory = os.path.join(upload_directory, userhash)
    if not os.path.isdir(user_directory):
        return 0

    return sum(os.path.getsize(os.path.join(user_directory, f)) for f in os.listdir(user_directory)) if os.path.isdir(user_directory) else 0

# Public User API
@app.route("/user/down/<string:userhash>/<string:filename>", methods = ["GET"])
def route_user_download(userhash: str, filename: str) -> None:
    if not app.db("uploads").can_download(session["userauth"]["userhash"], userhash, filename):
        return jsonify(code = 403, message = "Unauthorized."), 403

    filepath = os.path.join(upload_directory, userhash, secure_filename(filename))
    return send_file(filepath, conditional = True)

# Private Routes (User File Handling API)
@app.route("/user/api/files", methods = ["GET"])
def route_user_files() -> None:
    uh, uploaddb = session["userauth"]["userhash"], app.db("uploads")

    # Package up filedata
    recv = uploaddb.get_files(uh)
    sent = uploaddb.get_files_of_author(uh)

    # Calculate usage data
    usage = calculate_usage(uh)
    return jsonify(
        code = 200,
        recv = recv,
        sent = sent,
        usage = {"percent": round(usage / upload_limit, 2) * 100, "string": scale_bytes(usage)}
    ), 200

@app.route("/user/api/upload", methods = ["POST"])
def route_user_upload() -> None:
    if "file" not in request.files:
        return jsonify(code = 400, message = "No file sent to server."), 400

    file, uh = request.files["file"], session["userauth"]["userhash"]
    if not file.filename.strip():
        return jsonify(code = 400, message = "No filename provided.")

    file.seek(0, 2)
    filename, user_storage = secure_filename(file.filename), os.path.join(upload_directory, uh)
    if not os.path.isdir(user_storage):
        os.mkdir(user_storage)

    elif calculate_usage(uh) + file.tell() > upload_limit:
        print("YO THIS GUY DOESN'T HAVE THE SPACE FOR THAT!!!!")
        return jsonify(code = 400, message = "You don't have the space to upload that file."), 400

    file.seek(0, 0)
    file.save(os.path.join(user_storage, filename))
    return jsonify(code = 200, message = "File uploaded successfully."), 200

@app.route("/user/api/preupload", methods = ["GET"])
def route_user_preupload() -> None:
    try:
        uh = session["userauth"]["userhash"]
        fn, fs = request.args["name"], int(request.args["size"])
        if fs < 0:
            raise ValueError("Invalid filesize provided.")

        elif not fn.strip():
            raise ValueError("No filename provided.")

    except Exception as e:
        return jsonify(code = 400, message = str(e) if isinstance(e, ValueError) else "Missing required arguments."), 400

    # Calculate message
    message = "OK"
    if os.path.isfile(os.path.join(upload_directory, uh, secure_filename(fn))):
        message = "You already have an upload with that filename."

    elif calculate_usage(uh) + int(fs) > upload_limit:
        message = "You don't have the space to upload that file."

    code = 200 if message == "OK" else 400
    return jsonify(
        code = code,
        message = message
    ), code

@app.route("/user/api/fregister", methods = ["GET"])
def route_user_fileregister() -> None:
    try:
        filename, users = request.args["name"], request.args["users"].split(",")
        if not [u for u in users if u.strip()]:
            raise ValueError("No users provided to associate file with.")

        elif not filename.strip():
            raise ValueError("Empty filename provided.")

        # Check if file exists
        filepath = os.path.join(upload_directory, session["userauth"]["userhash"], secure_filename(filename))
        if not os.path.isfile(filepath):
            raise ValueError("No such file exists.")

        # Check if all users exist
        users = list(app.db("auth").check_users(users, return_hashes = True).values())
        if not all(users):
            raise ValueError("Some of the provided users do not exist.")

    except Exception as e:
        if isinstance(e, ValueError):
            return jsonify(code = 400, message = str(e)), 400

        return jsonify(code = 400), 400

    error = app.db("uploads").register_file(session["userauth"]["userhash"], filename, scale_bytes(os.path.getsize(filepath)), users)
    if error:
        return jsonify(code = 400, message = error), 400

    return jsonify(code = 200), 200

@app.route("/user/api/dfile", methods = ["GET"])
def route_user_deletefile() -> None:
    filename = request.args.get("name", "")
    if not filename.strip():
        return jsonify(code = 400, message = "No filename provided."), 400

    filepath = os.path.join(upload_directory, session["userauth"]["userhash"], secure_filename(filename))
    if not os.path.isfile(filepath):
        return jsonify(code = 404, message = "No such file exists."), 404

    app.db("uploads").delete_file(session["userauth"]["userhash"], filename)
    os.remove(filepath)
    return jsonify(code = 200), 200
