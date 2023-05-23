import os
from urllib.request import urlopen

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    my_ip = os.environ.get("MY_IP", get_public_ip_address())
    return f"Hello, this is my (public) IP address: {my_ip}"


def get_public_ip_address():
    with urlopen('https://api.ipify.org') as response:
        return response.read().decode('utf-8')


if __name__ == "__main__":
    app.run(host="0.0.0.0")
