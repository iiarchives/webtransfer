# Copyright 2022 iiPython

# Modules
import os
import time
import shutil
from dotenv import load_dotenv
from multiprocessing import Process
from werkzeug.utils import secure_filename

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_apscheduler import APScheduler
try:
    from flask_session import Session

except ImportError:
    Session = None

from .config import Config
from .database import DBHandler

# Pre-init
def rpath(path: str) -> str:
    return os.path.join(os.path.dirname(__file__), path)

load_dotenv()

# Flask app creation
app = Flask(
    "WebTransfer",
    template_folder = rpath("src/templates")
)
app.config.from_object(Config())
app.config["UPLOAD_DIRECTORY"] = os.path.abspath(rpath("../db/uploads"))

app.db = DBHandler(Bcrypt(app)).db
app.version = "1.0.8"
app.secret_key = os.getenv("SECRET_KEY")

if Session is not None:
    Session(app)

# APScheduler init
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Jinja env
@app.context_processor
def insert_globals() -> dict:
    return {"app": app}

# Post-initialization tasks
if os.getenv("WT_INITIALIZED") != "1":

    # Launch reaper
    @scheduler.task("interval", id = "reaper-interval", seconds = 60 * 5)
    def run_reaper():
        db = app.db("uploads")
        db.cursor.execute("SELECT userhash, filename FROM uploads WHERE expires <= ?", (round(time.time()),))
        for upload in db.cursor.fetchall():
            db.delete_file(upload["userhash"], upload["filename"])
            os.remove(os.path.join(app.config["UPLOAD_DIRECTORY"], upload["userhash"], secure_filename(upload["filename"])))

        db.cursor.execute("SELECT changes()")
        if db.cursor.fetchone()["changes()"] > 0:
            db.conn.commit()

    # Launch redis
    if Session is not None:
        redis_path = os.environ.get("REDIS_BINARY", shutil.which("redis-server"))
        if redis_path is None:
            exit("Failed to locate Redis server binary; you can specify this with the REDIS_BINARY environment variable")

        p = Process(target = os.system, args = (f"\"{redis_path}\" \"{os.path.join(os.path.dirname(__file__), 'redis.conf')}\"",))
        p.start()

    else:
        print("WARN: flask-session is not available, falling back to built-in session\n"
              "WARN: for security purposes, please install flask-session and relaunch WebTransfer")

    # Mark as initialized
    os.environ["WT_INITIALIZED"] = "1"

# Routes
from .routes import public  # noqa
from .routes.gateway import (  # noqa
    auth, files, public, friends, settings
)
