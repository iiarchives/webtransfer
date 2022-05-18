# Copyright 2022 iiPython

# Modules
import redis

# Configuration settings
class Config:
    MAX_CONTENT_LENGTH = 2 * (1024 ** 3)

    # Flask-Session
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.Redis(host = "localhost", port = 6379, db = 0)

    # Flask-APScheduler
    SCHEDULER_API_ENABLED = False
