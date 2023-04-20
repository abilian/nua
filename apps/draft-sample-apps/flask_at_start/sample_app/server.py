import os
from pathlib import Path

from flask import Flask, send_file

app = Flask(__name__)


@app.route("/")
def hello_world():
    path = Path(os.environ["WWW_DIR"]) / "test.html"
    print(path)
    return send_file(path)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
