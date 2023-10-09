import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    my_ip = os.environ["MY_IP"]
    return f"Hello, this is my IP address: {my_ip}"


if __name__ == "__main__":
    app.run(host="0.0.0.0")
