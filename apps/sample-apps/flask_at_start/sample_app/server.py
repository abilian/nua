import os

from flask import Flask, send_from_directory

app = Flask(__name__)


@app.route("/")
def hello_world():
    www = os.environ("WWW_DIR")
    return send_from_directory(www, "test.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
