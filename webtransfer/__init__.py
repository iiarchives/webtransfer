# Copyright 2022 iiPython

# Modules
import os
from flask import Flask
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt

from .database import DBHandler

# Initialization
def rpath(path: str) -> str:
    return os.path.join(os.path.dirname(__file__), path)

load_dotenv()

app = Flask(
    "WebTransfer",
    template_folder = rpath("src/templates")
)
app.config["MAX_CONTENT_LENGTH"] = 2 * (1024 ** 3)

app.db = DBHandler(Bcrypt(app)).db
app.version = "1.0.5"
app.secret_key = os.getenv("SECRET_KEY")

# Jinja env
@app.context_processor
def insert_globals() -> dict:
    return {"app": app}

# Routes
from .routes import public  # noqa
from .routes.gateway import (  # noqa
    auth, files, public, friends, settings
)
