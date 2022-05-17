# Copyright 2022 iiPython

# Modules
import os
import time
from flask import Flask
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from flask_apscheduler import APScheduler
from werkzeug.utils import secure_filename

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
app.version = "1.0.7"
app.secret_key = os.getenv("SECRET_KEY")

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Jinja env
@app.context_processor
def insert_globals() -> dict:
    return {"app": app}

# Launch reaper
if os.getenv("_WT_REAPER_LAUNCHED") != "1":
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

    os.environ["_WT_REAPER_LAUNCHED"] = "1"

# Routes
from .routes import public  # noqa
from .routes.gateway import (  # noqa
    auth, files, public, friends, settings
)
