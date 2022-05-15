# Copyright 2022 iiPython

# Modules
import os
import uuid
import time
import string
import sqlite3

# Initialization
database_directory = os.path.join(os.path.dirname(__file__), "../db")
if not os.path.isdir(database_directory):
    os.mkdir(database_directory)

def strip_punctuation(s: str) -> str:
    for c in string.punctuation:
        s = s.replace(c, "")

    return s

# Database class
class InheritedDB(object):
    def __init__(self, init: str, filename: str) -> None:
        self.conn = sqlite3.connect(os.path.join(database_directory, filename), check_same_thread = False)
        self.conn.row_factory = lambda c, r: {cl[0]: r[i] for i, cl in enumerate(c.description)}
        self.cursor = self.conn.cursor()
        self.cursor.execute(init)

class AuthenticationDB(InheritedDB):
    def __init__(self, handler, bcrypt) -> None:
        super().__init__("""
        CREATE TABLE IF NOT EXISTS users (
            username text,
            userlwrd text,
            password text,
            userhash text
        )
        """, "auth.db")
        self.handler = handler
        self.bcrypt = bcrypt

    def generate_user_hash(self) -> str | None:
        for i in range(5):
            uhash = uuid.uuid4().hex
            self.cursor.execute("SELECT username FROM users WHERE userhash=?", (uhash,))
            if not self.cursor.fetchone():
                return uhash

        return None

    def check_login(self, username: str, password: str) -> dict | None:
        self.cursor.execute("SELECT username, password, userhash FROM users WHERE userlwrd=?", (strip_punctuation(username.lower()),))
        data = self.cursor.fetchone()
        if not data:
            return None

        elif not self.bcrypt.check_password_hash(data["password"].encode("utf-8"), password):
            return None

        del data["password"]  # You don't want your hashed password hanging around in session storage, do you?
        return data

    def check_users(self, users: list, return_hashes: bool = False) -> dict:
        user_str = ",".join([f"'{strip_punctuation(u.lower())}'" for u in users])
        self.cursor.execute(f"""SELECT username, userlwrd, userhash FROM users WHERE userlwrd IN ({user_str}) OR userhash IN ({user_str})""")

        # Calculate
        data, entries = self.cursor.fetchall(), {}
        for u in users:
            ul = u.lower()
            results = [d for d in data if ul in [d["userlwrd"], d["userhash"]]]
            entries[u] = (results[0]["username"] if not return_hashes else results[0]["userhash"]) if results else None

        return entries

    def register(self, username: str, password: str) -> str | None:
        username_error = "username-too-short" if len(username) < 4 else "username-too-long" if len(username) > 32 else None
        if username_error is not None:
            return username_error

        elif [c for c in username if c in string.punctuation]:
            return "username-invalid"

        elif len(password) < 8:
            return "password-too-short"

        self.cursor.execute("SELECT username FROM users WHERE userlwrd=?", (username.lower(),))
        if self.cursor.fetchone():
            return "username-taken"

        password, user_hash = self.bcrypt.generate_password_hash(password).decode(), self.generate_user_hash()
        if user_hash is None:
            return "uuid-failure"  # Not gonna waste much CPU time on a single request, just retry it

        self.cursor.execute("INSERT INTO users VALUES (?,?,?,?)", (username, username.lower(), password, user_hash))
        self.conn.commit()

    def hash_to_username(self, userhash: str) -> str:
        self.cursor.execute("SELECT username FROM users WHERE userhash=?", (userhash,))
        return self.cursor.fetchone()["username"]

class UploadDB(InheritedDB):
    def __init__(self, handler, bcrypt) -> None:
        super().__init__("""
        CREATE TABLE IF NOT EXISTS uploads (
            userhash text,
            filename text,
            filesize text,
            recipients text,
            expires long
        )
        """, "uploads.db")
        self.handler = handler
        self.bcrypt = bcrypt

        # Initialization
        self.authdb = self.handler.db("auth")  # Nice locally cached version

    def register_file(self, user_hash: str, filename: str, filesize: str, recipients: str) -> str | None:
        self.cursor.execute("SELECT userhash FROM uploads WHERE userhash=? AND filename=?", (user_hash, filename))
        if self.cursor.fetchone():
            return "The specified filename is already registered."

        self.cursor.execute("INSERT INTO uploads VALUES (?,?,?,?,?)", (user_hash, filename, filesize, ",".join(recipients), round(time.time() + 86400)))
        self.conn.commit()

    def get_files(self, user_hash: str) -> list:
        # BEWARE: NORMALLY THIS WOULD COUNT AS SQL INJECTION, HOWEVER USER_HASH IS STORED IN SESSION DATA
        # THE USER HAS ABSOLUTELY NO CONTROL OVER THIS VARIABLE, AND THEREFOR THIS STATEMENT IS SAFE.
        self.cursor.execute(f"SELECT userhash, filename, filesize, expires FROM uploads WHERE instr(recipients, '{user_hash}') > 0")
        return [c | {"username": self.authdb.hash_to_username(c["userhash"])} for c in self.cursor.fetchall()]

    def get_files_of_author(self, user_hash: str) -> list:
        self.cursor.execute("SELECT userhash, filename, filesize, recipients, expires FROM uploads WHERE userhash=?", (user_hash,))
        return [
            c | {
                "username": self.authdb.hash_to_username(c["userhash"]),
                "recipients": [self.authdb.hash_to_username(r) for r in c["recipients"].split(",")]
            }
            for c in self.cursor.fetchall()
        ]

    def can_download(self, user_hash: str, author_hash: str, filename: str) -> bool:
        # BEWARE: NORMALLY THIS WOULD COUNT AS SQL INJECTION, HOWEVER USER_HASH IS STORED IN SESSION DATA
        # THE USER HAS ABSOLUTELY NO CONTROL OVER THIS VARIABLE, AND THEREFOR THIS STATEMENT IS SAFE.
        self.cursor.execute(f"SELECT filename FROM uploads WHERE userhash=? AND filename=? AND instr(recipients, '{user_hash}') > 0", (author_hash, filename))
        return bool(self.cursor.fetchone())

    def delete_file(self, user_hash: str, filename: str) -> None:
        self.cursor.execute("DELETE FROM uploads WHERE userhash=? AND filename=?", (user_hash, filename))
        self.conn.commit()

# Handler
class DBHandler(object):
    def __init__(self, bcrypt) -> None:
        self.bcrypt = bcrypt
        self.cache = {}
        self.mapping = {"auth": AuthenticationDB, "uploads": UploadDB}

    def db(self, key: str) -> InheritedDB:
        db = self.cache.get(key, self.mapping[key](self, self.bcrypt))
        if key not in self.cache:
            self.cache[key] = db

        return db
