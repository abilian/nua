import os

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


app.config["UPLOAD_PATH"] = os.environ.get("UPLOAD_PATH") or "/var/tmp/uploads"


def ensure_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


@app.route("/")
def index():
    ensure_path(app.config["UPLOAD_PATH"])
    files = os.listdir(app.config["UPLOAD_PATH"])
    return render_template("index.html", files=files)


@app.route("/", methods=["POST"])
def upload_files():
    ensure_path(app.config["UPLOAD_PATH"])
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename:
        uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], filename))
    return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def upload(filename):
    ensure_path(app.config["UPLOAD_PATH"])
    return send_from_directory(app.config["UPLOAD_PATH"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
