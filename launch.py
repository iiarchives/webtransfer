# Copyright 2022 iiPython

# Modules
from webtransfer import app

# Launch app
if __name__ == "__main__":
    app.run(
        host = "0.0.0.0",
        port = 8080,
        debug = True
    )
