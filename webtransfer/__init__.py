# Copyright 2022 iiPython

# Modules
import os
import time
from dotenv import load_dotenv
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

    # Mark as initialized
    os.environ["WT_INITIALIZED"] = "1"

# Routes
from .routes import public  # noqa
from .routes.gateway import (  # noqa
    auth, files, public, friends, settings
)
