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
app.config["UPLOAD_DIRNAME"] = os.environ.get("UPLOAD_DIRNAME") or "upload"


def ensure_path(path: Path):
    if path.is_dir():
        return
    if not path.parent.is_dir():
        raise ValueError(f"The bind volume '{path.parent}' should already exist")
    path.mkdir()


def upload_path() -> Path:
    upload_dir = Path(MOUNT_POINT) / app.config["UPLOAD_DIRNAME"]
    ensure_path(upload_dir)
    return upload_dir


def list_dir(path: Path) -> list:
    return [
        p.name for p in path.glob("*") if p.is_file() and not p.name.startswith(".")
    ]


@app.route("/")
def index():
    upload = upload_path()
    files = list_dir(upload)
    return render_template("index.html", files=files, upload=str(upload))


@app.route("/", methods=["POST"])
def upload_files():
    upload = upload_path()
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename:
        uploaded_file.save(upload / filename)
    return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def upload(filename):
    return send_from_directory(upload_path(), filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
