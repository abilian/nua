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
app.config["UPLOAD_PATH"] = "uploads"


@app.route("/")
def index():
    files = os.listdir(app.config["UPLOAD_PATH"])
    return render_template("index.html", files=files)


@app.route("/", methods=["POST"])
def upload_files():
    uploaded_file = request.files["file"]
    filename = secure_filename(uploaded_file.filename)
    if filename:
        uploaded_file.save(os.path.join(app.config["UPLOAD_PATH"], filename))
    return redirect(url_for("index"))


@app.route("/uploads/<filename>")
def upload(filename):
    return send_from_directory(app.config["UPLOAD_PATH"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
