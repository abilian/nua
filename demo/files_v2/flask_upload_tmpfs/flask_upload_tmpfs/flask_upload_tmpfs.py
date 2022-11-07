import os
from pathlib import Path

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)

MOUNT_POINT = Path("/var/tmp/mount_point")


def list_dir() -> list:
    return [
        p.name
        for p in MOUNT_POINT.glob("*")
        if p.is_file() and not p.name.startswith(".")
    ]


@app.route("/")
def index():
    files = list_dir()
    return render_template("index.html", files=files, upload=str(MOUNT_POINT))


@app.route("/", methods=["POST"])
def upload_files():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename:
        uploaded_file.save(MOUNT_POINT / filename)
    return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def upload(filename):
    return send_from_directory(MOUNT_POINT, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
